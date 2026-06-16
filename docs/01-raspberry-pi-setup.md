# Step 1 — Raspberry Pi Setup

This guide covers everything needed to get the Raspberry Pi ready to run the sorter.

> **Machine:** Raspberry Pi (Raspbian ARM64)

### 1.1 Clone the repository

```bash
git clone https://github.com/ITLab-CC/Sorter
cd Sorter
```

## 1.1 Install system dependencies

```bash
sudo apt update
sudo apt install -y \
    udev \
    ethtool \
    libusb-1.0-0 \
    iproute2 \
    iputils-ping \
    net-tools \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    curl \
    git \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    protobuf-compiler \
    libedgetpu1-max
```

## 1.2 Install pyenv and Python 3.10

```bash
curl https://pyenv.run | bash

LINE1='export PYENV_ROOT="$HOME/.pyenv"'
LINE2='command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
LINE3='eval "$(pyenv init -)"'
grep -qF "$LINE1" ~/.bashrc || echo "$LINE1" >> ~/.bashrc
grep -qF "$LINE2" ~/.bashrc || echo "$LINE2" >> ~/.bashrc
grep -qF "$LINE3" ~/.bashrc || echo "$LINE3" >> ~/.bashrc
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

pyenv install 3.10.20
pyenv local 3.10.20
```

## 1.3 Create a virtual environment and install Python packages

```bash
python3.10 -m venv .venv-3.10
export SPINNAKER_GENTL64_CTI=/opt/spinnaker/lib/spinnaker-gentl/Spinnaker_GenTL.cti
.venv-3.10/bin/pip install --upgrade pip setuptools wheel
.venv-3.10/bin/pip install -r ./actuator/requirements-3.10.txt
.venv-3.10/bin/pip install -r ./sensor/requirements-3.10.txt
.venv-3.10/bin/pip install -r requirements-3.10.txt
```

## 1.4 Install Coral Edge TPU runtime (ARM64)

```bash
mkdir -p ~/coral-wheels
wget -O ~/coral-wheels/tflite_runtime-2.12.0-cp310-cp310-linux_aarch64.whl \
  "https://github.com/oberluz/pycoral/releases/download/2.12.0/tflite_runtime-2.12.0-cp310-cp310-linux_aarch64.whl"

wget -O ~/coral-wheels/pycoral-2.12.0-cp310-cp310-linux_aarch64.whl \
  "https://github.com/oberluz/pycoral/releases/download/2.12.0/pycoral-2.12.0-cp310-cp310-linux_aarch64.whl"

.venv-3.10/bin/pip install ~/coral-wheels/tflite_runtime-2.12.0-cp310-cp310-linux_aarch64.whl
.venv-3.10/bin/pip install ~/coral-wheels/pycoral-2.12.0-cp310-cp310-linux_aarch64.whl
```

## 1.5 Install the Spinnaker SDK (camera driver)

Download both the SDK and the Python bindings from the [Spinnaker SDK download page](https://www.teledynevisionsolutions.com/support/support-center/software-firmware-downloads/iis/spinnaker-sdk-download/spinnaker-sdk--download-files/?pn=Spinnaker+SDK&vn=Spinnaker+SDK) and place them in the `sensor/` folder.

You need these two files (ARM64):

- `spinnaker-4.3.0.189-Ubuntu22.04-arm64-pkg.tar.gz` (Linux Ubuntu 22.04 --ARM64)
- `spinnaker_python-4.3.0.189-cp310-cp310-linux_aarch64.tar.gz` (Linux Ubuntu 22.04 -- ARM64 Python 3.10)

### Extract and install the SDK

```bash
mkdir -p sensor/spinnaker_sdk sensor/spinnaker_python
tar -xzvf sensor/spinnaker-4.3.0.189-Ubuntu22.04-arm64-pkg.tar.gz -C sensor/spinnaker_sdk
tar -xzvf sensor/spinnaker_python-4.3.0.189-cp310-cp310-linux_aarch64.tar.gz -C sensor/spinnaker_python

cd sensor/spinnaker_sdk/spinnaker-4.3.0.189-arm64/
./install_spinnaker_arm.sh
```

### Install the Python bindings

```bash
cd ../../spinnaker_python
../../.venv-3.10/bin/pip install spinnaker_python-4.3.0.189-cp310-cp310-linux_aarch64.whl
```

### Clean up

```bash
cd ../..
rm -rf sensor/spinnaker_python sensor/spinnaker_sdk
```

## 1.6 Set a safe GPIO state for the elevator stepper

At power-on the GPIO pins float until a program drives them. For the elevator
stepper driver this means the `ENABLE` pin can drift and energise the driver,
while the floating `STEP` pin picks up electrical noise — causing the motor to
hum or twitch/rotate on its own **even when no program is running**.

To hold the driver in a safe, defined state from boot, append the following
lines to the bottom of `/boot/firmware/config.txt` (older Raspberry Pi OS:
`/boot/config.txt`):

```bash
sudo tee -a /boot/firmware/config.txt > /dev/null <<'EOF'

# Elevator stepper driver: hold pins in a safe state from power-on so the
# motor does not twitch/rotate while no program is running.
# 17=ENABLE (active-low -> drive HIGH = disabled), 22=STEP, 27=DIR.
gpio=17=op,dh
gpio=22=op,dl
gpio=27=op,dl
EOF
```

Then reboot for the settings to take effect:

```bash
sudo reboot
```

> **Note:** `17` is the `ENABLE` pin. This assumes an active-low driver
> (A4988/DRV8825), so it is driven HIGH (`dh`) to keep the driver disabled.
> If your driver enables on HIGH instead, change `gpio=17=op,dh` to
> `gpio=17=op,dl`.

---

**Previous:** [Step 0 — Build the Sorter](00-build-the-sorter.md)
**Next:** [Step 2 — Training PC Setup](02-training-pc-setup.md)

[**Home**](../README.md)