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
_DEFAULT_BGR = (255, 255, 255)
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
        # Set while the user has pressed START and sorting should run.
        self.running = threading.Event()
        # Set when the window is closed / the app should exit entirely.
        self.quit = threading.Event()
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
        root.bind("<Escape>", lambda _e: root.attributes("-fullscreen", False))

        # ── Fit layout to the actual screen ───────────────────────────
        # The display can be small (e.g. 800x480 on a Pi DSI panel), so
        # size everything relative to the real screen dimensions instead
        # of using fixed pixel values that overflow the visible area.
        # Compute the layout from the *current* screen dimensions. Wrapped in
        # a function so it can be re-run later: on autostart XWayland may
        # report stale/placeholder screen dimensions until the compositor has
        # finished mapping the window.
        def _compute_layout() -> dict:
            root.update_idletasks()
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            # Landscape layout: marble image fills the full height on the left
            # (kept as large as possible so it stays sharp), and the banner +
            # counters live in the leftover column on the right. This avoids
            # shrinking the image to make room for stacked text bars.
            ph = sh
            pw = int(ph * 4 / 3)
            # Keep at least a minimum info column; clamp the image if needed.
            min_panel_w = 150
            if pw > sw - min_panel_w:
                pw = sw - min_panel_w
                ph = int(pw * 3 / 4)
            panel_w = max(min_panel_w, sw - pw)
            return {
                "sw": sw, "sh": sh, "pw": pw, "ph": ph, "panel_w": panel_w,
                # Scale fonts to the info-panel width so the text fits without
                # overflowing the column.
                "banner_font": max(12, int(panel_w * 0.13)),
                "stats_font": max(11, int(panel_w * 0.10)),
                "button_font": max(12, int(panel_w * 0.11)),
            }

        _lay = _compute_layout()
        screen_w, screen_h = _lay["sw"], _lay["sh"]
        panel_w = _lay["panel_w"]
        banner_font = _lay["banner_font"]
        stats_font = _lay["stats_font"]
        self._pw, self._ph = _lay["pw"], _lay["ph"]

        # Some window managers (common on the Raspberry Pi) ignore the
        # "-fullscreen" attribute when it is set before the window is mapped.
        # Force an explicit full-screen geometry first, then re-assert the
        # fullscreen attribute once the window has actually been realised.
        root.geometry(f"{screen_w}x{screen_h}+0+0")
        root.overrideredirect(True)
        root.attributes("-fullscreen", True)

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
            text="Press\nSTART",
            font=("DejaVu Sans", banner_font, "bold"),
            fg="white",
            bg="black",
            wraplength=panel_w - 10,
            justify="center",
            pady=8,
        )
        # Banner is packed *last* (see below) so the button/stats reserve their
        # space first and the wrapping banner can never push the button off-screen.

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

        # ── Start / Stop control ──────────────────────────────────────
        button_font = max(12, int(panel_w * 0.11))

        def _on_start() -> None:
            # Clear all statistics before a new sorting session.
            _counts["red"] = _counts["green"] = _counts["other"] = 0
            stats_label.config(text="Red: 0\nGreen: 0\nOther: 0")
            banner.config(text="Sorting…", fg="white")
            canvas.delete("all")
            _img_ref[0] = None
            self.running.set()
            toggle_btn.config(text="STOP", bg="#AA2222", activebackground="#CC3333",
                              command=_on_stop)
            toggle_btn.lift()
            root.update_idletasks()

        def _on_stop() -> None:
            self.running.clear()
            banner.config(text="Stopped", fg="red")
            toggle_btn.config(text="START", bg="#22AA22", activebackground="#33CC33",
                              command=_on_start)
            toggle_btn.lift()
            root.update_idletasks()

        toggle_btn = tk.Button(
            panel,
            text="START",
            font=("DejaVu Sans", button_font, "bold"),
            fg="white",
            bg="#22AA22",
            activebackground="#33CC33",
            activeforeground="white",
            relief="raised",
            bd=4,
            command=_on_start,
        )
        # Pack the button towards the bottom (above the stats) so its slot is
        # reserved before the banner. This guarantees the button stays fully
        # visible even when the banner text wraps to several lines.
        toggle_btn.pack(side="bottom", fill="x", padx=8, pady=12, ipady=10)
        toggle_btn.lift()

        # Banner is packed last and absorbs the leftover space in the middle,
        # so its wrapped text grows into empty area instead of over the button.
        banner.pack(side="top", fill="both", expand=True, pady=(12, 0))

        # ── Keep the window fullscreen on autostart ───────────────────
        # The compositor maps the window asynchronously, so a single
        # fullscreen attempt is unreliable (the window can stay windowed,
        # as seen on boot). Re-assert it for the first few seconds and
        # re-apply the layout if the reported screen size changes.
        def _apply_layout(lay: dict) -> None:
            self._pw, self._ph = lay["pw"], lay["ph"]
            canvas.config(width=lay["pw"], height=lay["ph"])
            panel.config(width=lay["panel_w"], height=lay["sh"])
            banner.config(font=("DejaVu Sans", lay["banner_font"], "bold"),
                          wraplength=lay["panel_w"] - 10)
            stats_label.config(font=("DejaVu Sans", lay["stats_font"]),
                               wraplength=lay["panel_w"] - 10)
            toggle_btn.config(font=("DejaVu Sans", lay["button_font"], "bold"))

        _applied_size = [(screen_w, screen_h)]

        def _force_fullscreen() -> None:
            lay = _compute_layout()
            if (lay["sw"], lay["sh"]) != _applied_size[0]:
                _applied_size[0] = (lay["sw"], lay["sh"])
                _apply_layout(lay)
            root.geometry(f"{lay['sw']}x{lay['sh']}+0+0")
            root.attributes("-fullscreen", True)
            root.attributes("-topmost", True)
            root.lift()
            root.focus_force()
            # override-redirect windows don't always get an expose event from
            # the WM, so force a full redraw of all widgets (incl. the button).
            root.update()

        def _fullscreen_watchdog(remaining: int) -> None:
            _force_fullscreen()
            if remaining > 0 and not self.quit.is_set():
                root.after(300, _fullscreen_watchdog, remaining - 1)

        root.after(100, _fullscreen_watchdog, 20)

        def _on_close() -> None:
            self.running.clear()
            self.quit.set()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", _on_close)
        root.bind("<q>", lambda _e: _on_close())

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

                # Keep the control button on top of any redraw.
                toggle_btn.lift()

            root.after(50, _poll)

        root.after(50, _poll)
        root.mainloop()
