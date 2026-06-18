# Step 5 — Run the Sorter

You now have a trained Edge TPU model. Time to sort some marbles.

> **Machine:** Raspberry Pi

## 5.1 Get a model into `my-models/`

The sorter loads its model from the `my-models/` folder (which is git-ignored). You have two options:

### Option A — Use the included pretrained model (no training required)

If you don't want to train your own model, a **pretrained, ready-to-use** model ships with the project in `my-models-example/`. Just copy its contents into `my-models/`:

```bash
# From the project root, on the Raspberry Pi
mkdir -p my-models
cp my-models-example/marbel_coral.tflite my-models-example/labels.txt my-models/
```

That's it — you can skip Steps 2–4 entirely. See [`my-models-example/README.md`](../my-models-example/README.md) for details about the model.

### Option B — Use your own trained model

If you completed [Step 4 — Train the Model](04-train-model.md), transfer `my-models/marbel_coral.tflite` and `my-models/labels.txt` from the training PC to the Raspberry Pi project directory (inside `my-models/`).

## 5.2 Start the sorter

Make sure the camera, Coral USB Accelerator, motors, and sensors are all connected, then run:

```bash
sudo .venv-3.10/bin/python main.py
```

Enjoy your sorted marbles!

## 5.3 Run automatically on boot (autostart)

To make the sorter start by itself once the desktop appears, use the **labwc** autostart script (Raspberry Pi OS Bookworm/trixie use the labwc Wayland compositor).

We run the app inside a detached [`screen`](https://www.gnu.org/software/screen/) session named `sorter`, so you can attach later to see its console output.

1. Make sure `screen` is installed:

   ```bash
   sudo apt install screen
   ```

2. Create the file `~/.config/labwc/autostart` with the following contents (adjust the paths if your project lives elsewhere):

   ```sh
   #!/bin/sh
   # Start the marble sorter app in a detached screen session after the desktop comes up
   cd /home/sorter/Documents/Sorter
   screen -dmS sorter sudo --preserve-env=WAYLAND_DISPLAY,XDG_RUNTIME_DIR .venv-3.10/bin/python main.py
   ```

   - `screen -dmS sorter` starts a **d**etached, na**m**ed (`sorter`) session in the background.
   - `sudo --preserve-env=WAYLAND_DISPLAY,XDG_RUNTIME_DIR` lets the root process reach the Wayland display (required because the app runs with `sudo` under Wayland). For this to work without a password prompt, passwordless `sudo` must be configured (it is by default on Raspberry Pi OS for the default user).

3. Make it executable:

   ```bash
   chmod +x ~/.config/labwc/autostart
   ```

4. Test it without rebooting, then reboot to confirm:

   ```bash
   ~/.config/labwc/autostart
   screen -ls          # should list the "sorter" session
   sudo reboot
   ```

### Managing the running session

| Action | Command |
| --- | --- |
| Attach to / view the app console | `screen -r sorter` |
| Detach again (leave it running) | press `Ctrl+a` then `d` |
| List sessions | `screen -ls` |
| Stop the sorter | `screen -XS sorter quit` |

---

**Previous:** [Step 4 — Train the Model](04-train-model.md)
**Back to:** [README](../README.md)

[**Home**](../README.md)