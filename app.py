import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import scrcpy


import cv2
import numpy as np
from PIL import Image, ImageTk

try:
    import adbutils
    import scrcpy
except ImportError as exc:
    raise SystemExit(
        "Missing required dependencies. Install with: pip install -r requirements.txt"
    ) from exc


class MirrorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Python Android Screen Mirroring")
        self.root.geometry("980x640")

        self.client = None
        self.frame_queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=1)
        self.running = False

        self.device_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Disconnected")

        self._build_ui()
        self.refresh_devices()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Device:").pack(side=tk.LEFT)
        self.device_combo = ttk.Combobox(top, width=40, textvariable=self.device_var, state="readonly")
        self.device_combo.pack(side=tk.LEFT, padx=(8, 8))

        ttk.Button(top, text="Refresh", command=self.refresh_devices).pack(side=tk.LEFT)
        ttk.Button(top, text="Start Mirror", command=self.start_mirror).pack(side=tk.LEFT, padx=(8, 8))
        ttk.Button(top, text="Stop", command=self.stop_mirror).pack(side=tk.LEFT)

        ttk.Label(top, textvariable=self.status_var, foreground="blue").pack(side=tk.RIGHT)

        self.canvas = tk.Label(self.root, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        tips = (
            "Tips: Enable Developer Options + USB debugging on your phone, "
            "connect via USB, and make sure adb can detect the device."
        )
        ttk.Label(self.root, text=tips, wraplength=900, foreground="gray").pack(fill=tk.X, padx=10, pady=(0, 10))

    def refresh_devices(self) -> None:
        try:
            devices = adbutils.adb.device_list()
            serials = [d.serial for d in devices]
        except Exception as exc:
            messagebox.showerror("ADB Error", f"Unable to query devices: {exc}")
            serials = []

        self.device_combo["values"] = serials
        if serials:
            self.device_var.set(serials[0])
            self.status_var.set(f"Found {len(serials)} device(s)")
        else:
            self.device_var.set("")
            self.status_var.set("No devices found")

    def start_mirror(self) -> None:
        if self.running:
            return

        serial = self.device_var.get().strip()
        if not serial:
            messagebox.showwarning("No device", "Please connect a device and click Refresh.")
            return

        try:
            device = adbutils.adb.device(serial=serial)
            self.client = scrcpy.Client(device=device, max_fps=30, bitrate=8_000_000)
            self.client.add_listener(scrcpy.EVENT_FRAME, self.on_frame)

            self.running = True
            threading.Thread(target=self.client.start, daemon=True).start()
            self.status_var.set(f"Mirroring: {serial}")
            self.update_canvas()
        except Exception as exc:
            self.running = False
            messagebox.showerror("Start failed", f"Could not start mirroring: {exc}")

    def stop_mirror(self) -> None:
        if self.client is not None:
            try:
                self.client.stop()
            except Exception:
                pass

        self.running = False
        self.client = None
        self.status_var.set("Stopped")

    def on_frame(self, frame: np.ndarray) -> None:
        if frame is None:
            return

        if self.frame_queue.full():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                pass

        self.frame_queue.put_nowait(frame)

    def update_canvas(self) -> None:
        if not self.running:
            return

        try:
            frame = self.frame_queue.get_nowait()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            canvas_w = max(self.canvas.winfo_width(), 1)
            canvas_h = max(self.canvas.winfo_height(), 1)

            h, w, _ = frame_rgb.shape
            scale = min(canvas_w / w, canvas_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            resized = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)

            image = Image.fromarray(resized)
            photo = ImageTk.PhotoImage(image=image)

            self.canvas.configure(image=photo)
            self.canvas.image = photo
        except queue.Empty:
            pass
        except Exception:
            pass

        self.root.after(15, self.update_canvas)


if __name__ == "__main__":
    root = tk.Tk()
    app = MirrorApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_mirror(), root.destroy()))
    root.mainloop()
