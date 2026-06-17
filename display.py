"""Marble Sorter – Raspberry Pi display frontend (pure Python / tkinter).

Runs in its own daemon thread. Call ``update_detection()`` whenever a marble
is classified. The last detected marble stays on screen until the next one
arrives. The window is fullscreen and uses only tkinter + Pillow.
"""

import glob
import os
import queue
import threading
import time
import tkinter as tk
from typing import Callable, Optional, Tuple

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

    def __init__(
        self,
        preview_width: int = 640,
        preview_height: int = 480,
        sleep_timeout: float = 300.0,
        on_sleep: Optional[Callable[[], None]] = None,
        on_wake: Optional[Callable[[], None]] = None,
    ) -> None:
        self._pw = preview_width
        self._ph = preview_height
        self._queue: queue.Queue = queue.Queue(maxsize=2)
        # Set while the user has pressed START and sorting should run.
        self.running = threading.Event()
        # Set when the window is closed / the app should exit entirely.
        self.quit = threading.Event()
        # ── Sleep / screensaver ───────────────────────────────────────
        # After `sleep_timeout` seconds without any touch interaction (and
        # while not actively sorting) the screen is blanked and the optional
        # `on_sleep` callback fires (used to switch the NeoPixels off). Any
        # touch wakes everything back up via `on_wake`.
        self._sleep_timeout = sleep_timeout
        self._on_sleep = on_sleep
        self._on_wake = on_wake
        # Set while the display is asleep (screen blanked).
        self.sleeping = threading.Event()
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
            fg="#33FF33",
            bg="black",
            wraplength=panel_w - 10,
            justify="center",
            pady=8,
        )
        # Banner is packed *last* (see below) so the button/stats reserve their
        # space first and the wrapping banner can never push the button off-screen.

        stats_frame = tk.Frame(panel, bg="black")
        stats_frame.pack(side="bottom", fill="x", pady=(0, 12))

        stats_red = tk.Label(
            stats_frame,
            text="Red: 0",
            font=("DejaVu Sans", stats_font),
            fg="#FF3333",
            bg="black",
        )
        stats_red.pack()

        stats_green = tk.Label(
            stats_frame,
            text="Green: 0",
            font=("DejaVu Sans", stats_font),
            fg="#33FF33",
            bg="black",
        )
        stats_green.pack()

        stats_other = tk.Label(
            stats_frame,
            text="Other: 0",
            font=("DejaVu Sans", stats_font),
            fg="white",
            bg="black",
        )
        stats_other.pack()

        _img_ref: list = [None]
        _counts: dict = {"red": 0, "green": 0, "other": 0}

        # ── Start / Stop control ──────────────────────────────────────
        button_font = max(12, int(panel_w * 0.11))

        def _on_start() -> None:
            # Clear all statistics before a new sorting session.
            _counts["red"] = _counts["green"] = _counts["other"] = 0
            stats_red.config(text="Red: 0")
            stats_green.config(text="Green: 0")
            stats_other.config(text="Other: 0")
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
            stats_red.config(font=("DejaVu Sans", lay["stats_font"]))
            stats_green.config(font=("DejaVu Sans", lay["stats_font"]))
            stats_other.config(font=("DejaVu Sans", lay["stats_font"]))
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

        # ── Sleep mode (screen blanking + LED off after inactivity) ────
        # A black frame that covers the entire window while asleep. It sits
        # on top of everything and swallows the first touch (which wakes us).
        sleep_overlay = tk.Frame(root, bg="black", cursor="none")

        _last_activity = [time.monotonic()]

        def _set_backlight(on: bool) -> None:
            """Best-effort backlight power control (Pi DSI/HDMI panels).

            Writing the framebuffer blank state to ``bl_power`` (0 = on,
            1 = off). Silently ignored if the sysfs node is missing or not
            writable, in which case the black overlay still hides the screen.
            """
            try:
                for path in glob.glob("/sys/class/backlight/*/bl_power"):
                    with open(path, "w") as fh:
                        fh.write("0" if on else "1")
            except Exception:
                pass

        def _go_to_sleep() -> None:
            if self.sleeping.is_set():
                return
            self.sleeping.set()
            if self._on_sleep is not None:
                try:
                    self._on_sleep()
                except Exception:
                    pass
            sleep_overlay.place(x=0, y=0, relwidth=1, relheight=1)
            sleep_overlay.lift()
            _set_backlight(False)

        def _wake() -> None:
            _last_activity[0] = time.monotonic()
            if not self.sleeping.is_set():
                return
            self.sleeping.clear()
            _set_backlight(True)
            sleep_overlay.place_forget()
            if self._on_wake is not None:
                try:
                    self._on_wake()
                except Exception:
                    pass
            toggle_btn.lift()

        def _on_interaction(_e=None) -> None:
            if self.sleeping.is_set():
                _wake()
            else:
                _last_activity[0] = time.monotonic()

        # Any touch (tap = Button press), release or key resets the timer or
        # wakes the screen. Bound on the root so it catches events anywhere,
        # including on the black overlay.
        for seq in ("<Button>", "<ButtonRelease>", "<Key>"):
            root.bind(seq, _on_interaction, add="+")
        sleep_overlay.bind("<Button>", _on_interaction, add="+")

        def _sleep_watchdog() -> None:
            if self.quit.is_set():
                return
            if not self.sleeping.is_set():
                # Never sleep while actively sorting – keep the timer fresh.
                if self.running.is_set():
                    _last_activity[0] = time.monotonic()
                elif time.monotonic() - _last_activity[0] >= self._sleep_timeout:
                    _go_to_sleep()
            root.after(1000, _sleep_watchdog)

        root.after(1000, _sleep_watchdog)

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
                stats_red.config(text=f"Red: {_counts['red']}")
                stats_green.config(text=f"Green: {_counts['green']}")
                stats_other.config(text=f"Other: {_counts['other']}")

                # Keep the control button on top of any redraw.
                toggle_btn.lift()

            root.after(50, _poll)

        root.after(50, _poll)
        root.mainloop()
