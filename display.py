"""Marble Sorter – Raspberry Pi display frontend (pure Python / tkinter).

Runs in its own daemon thread. Call ``update_detection()`` whenever a marble
is classified. The last detected marble stays on screen until the next one
arrives. The window is fullscreen and uses only tkinter + Pillow.
"""

import glob
import os
import queue
import threading
import tkinter as tk
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk


# ---------------------------------------------------------------------------
# Colour map: label → BGR border colour + hex label colour
# ---------------------------------------------------------------------------
_COLOUR_MAP: dict[str, Tuple[Tuple[int, int, int], str]] = {
    "red":   ((0,   0,   220), "#FF3333"),
    "green": ((0,   200,   0), "#33FF33"),
}
_DEFAULT_BGR = (0, 200, 255)
_DEFAULT_HEX = "#FFDD00"

_BORDER_THICKNESS = 8   # px, border drawn around the image


class MarbleDisplay:
    """Fullscreen tkinter display for the marble sorter.

    Only ``update_detection()`` and ``close()`` are needed.
    All Tk calls happen inside the dedicated daemon thread – the sorting
    loop is never blocked and never touches Tk objects directly.
    """

    def __init__(self, preview_width: int = 640, preview_height: int = 480) -> None:
        self._pw = preview_width
        self._ph = preview_height
        self._queue: queue.Queue = queue.Queue(maxsize=2)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_detection(
        self,
        frame_bgr: np.ndarray,
        label: str,
        confidence: float,
        bbox: Optional[Tuple[int, int, int, int]] = None,
    ) -> None:
        """Push a new detection to the display.

        Args:
            frame_bgr:  OpenCV BGR image.
            label:      Class label, e.g. ``"red"`` or ``"green"``.
            confidence: Confidence 0–100.
            bbox:       Optional ``(x, y, w, h)`` bounding box in image
                        coordinates. When *None* a border wraps the whole image.
        """
        self._post({
            "state":      "detection",
            "frame":      frame_bgr.copy(),
            "label":      label,
            "confidence": confidence,
            "bbox":       bbox,
        })

    def close(self) -> None:
        """Destroy the window (called on shutdown)."""
        self._post({"state": "quit"})

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _post(self, msg: dict) -> None:
        try:
            self._queue.put_nowait(msg)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(msg)
            except queue.Full:
                pass

    def _run(self) -> None:
        if not os.environ.get("DISPLAY"):
            os.environ["DISPLAY"] = ":0"
        if not os.environ.get("XAUTHORITY"):
            candidates = (
                glob.glob("/home/*/.Xauthority")
                + glob.glob("/run/user/*/gdm/Xauthority")
                + ["/root/.Xauthority"]
            )
            for path in candidates:
                if os.path.exists(path):
                    os.environ["XAUTHORITY"] = path
                    break

        root = tk.Tk()
        root.title("Marble Sorter")
        root.configure(bg="black")
        root.attributes("-fullscreen", True)
        root.bind("<Escape>", lambda _e: root.attributes("-fullscreen", False))

        # ── Fit layout to the actual screen ───────────────────────────
        # The display can be small (e.g. 800x480 on a Pi DSI panel), so
        # size everything relative to the real screen dimensions instead
        # of using fixed pixel values that overflow the visible area.
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()

        # Landscape layout: marble image fills the full height on the left
        # (kept as large as possible so it stays sharp), and the banner +
        # counters live in the leftover column on the right. This avoids
        # shrinking the image to make room for stacked text bars.
        ph = screen_h
        pw = int(ph * 4 / 3)
        # Keep at least a minimum info column; clamp the image if needed.
        min_panel_w = 150
        if pw > screen_w - min_panel_w:
            pw = screen_w - min_panel_w
            ph = int(pw * 3 / 4)
        self._pw, self._ph = pw, ph
        panel_w = max(min_panel_w, screen_w - pw)

        # Scale fonts to the info-panel width so the text fits without
        # overflowing the column.
        banner_font = max(12, int(panel_w * 0.13))
        stats_font = max(11, int(panel_w * 0.10))

        # ── Layout ────────────────────────────────────────────────────
        # Left:  marble image (full height)
        # Right: label/confidence banner (top) + running counters (bottom)

        canvas = tk.Canvas(
            root,
            width=self._pw,
            height=self._ph,
            bg="#111111",
            highlightthickness=0,
        )
        canvas.pack(side="left")

        panel = tk.Frame(root, bg="black", width=panel_w, height=screen_h)
        panel.pack(side="right", fill="both", expand=True)
        panel.pack_propagate(False)

        banner = tk.Label(
            panel,
            text="Waiting\nfor marble…",
            font=("DejaVu Sans", banner_font, "bold"),
            fg="white",
            bg="black",
            wraplength=panel_w - 10,
            justify="center",
            pady=8,
        )
        banner.pack(side="top", fill="x", pady=(12, 0))

        stats_label = tk.Label(
            panel,
            text="Red: 0\nGreen: 0\nOther: 0",
            font=("DejaVu Sans", stats_font),
            fg="#AAAAAA",
            bg="black",
            wraplength=panel_w - 10,
            justify="center",
            pady=8,
        )
        stats_label.pack(side="bottom", fill="x", pady=(0, 12))

        _img_ref: list = [None]
        _counts: dict = {"red": 0, "green": 0, "other": 0}

        def _make_photo(frame_bgr: np.ndarray, bgr_col: Tuple[int, int, int],
                        bbox: Optional[Tuple[int, int, int, int]]) -> ImageTk.PhotoImage:
            img = frame_bgr.copy()
            t = _BORDER_THICKNESS
            if bbox is not None:
                x, y, w, h = bbox
                cv2.rectangle(img, (x, y), (x + w, y + h), bgr_col, t)
            else:
                cv2.rectangle(img, (t, t), (img.shape[1] - t, img.shape[0] - t), bgr_col, t * 2)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(img_rgb).resize((self._pw, self._ph), Image.LANCZOS)
            return ImageTk.PhotoImage(pil)

        def _poll() -> None:
            try:
                msg = self._queue.get_nowait()
            except queue.Empty:
                root.after(50, _poll)
                return

            if msg["state"] == "quit":
                root.destroy()
                return

            if msg["state"] == "detection":
                label      = msg["label"]
                confidence = msg["confidence"]
                frame      = msg["frame"]
                bbox       = msg.get("bbox")

                bgr_col, hex_col = _COLOUR_MAP.get(label, (_DEFAULT_BGR, _DEFAULT_HEX))

                photo = _make_photo(frame, bgr_col, bbox)
                canvas.delete("all")
                canvas.create_image(self._pw // 2, self._ph // 2, image=photo, anchor="center")
                _img_ref[0] = photo

                banner.config(
                    text=f"Detected: {label.upper()}   {confidence:.1f}%",
                    fg=hex_col,
                )

                key = label if label in _counts else "other"
                _counts[key] += 1
                stats_label.config(
                    text=f"Red: {_counts['red']}\nGreen: {_counts['green']}\nOther: {_counts['other']}"
                )

            root.after(50, _poll)

        root.after(50, _poll)
        root.mainloop()
