# Step 2 — Training PC Setup

This guide sets up the PC you will use to train the AI model. You only need to do this once.

> **Machine:** PC with an NVIDIA GPU (Linux recommended)

## Requirements
Setup a PC which will be used for training the AI model. It should have an NVIDIA GPU and be running Linux. We tested this setup using ubuntu 24. It is also required to install the NVIDIA driver in a advance.

## 2.1 Clone the repository

```bash
git clone https://github.com/ITLab-CC/Sorter
cd Sorter
```

## 2.2 Install Docker

```bash
curl -sSL https://get.docker.com | sudo sh
```

## 2.3 Install the NVIDIA Container Toolkit

This lets Docker containers access the GPU.

```bash
sudo apt-get update && sudo apt-get install -y --no-install-recommends \
   ca-certificates \
   curl \
   gnupg2

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update

export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.19.0-1
sudo apt-get install -y \
    nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}

sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## 2.4 Build the training Docker image

```bash
sudo docker build -f Dockerfile.train -t sorter-train:latest .
```

This image contains TensorFlow 2.11, the TF Object Detection API, the pretrained SSD MobileNet V2 checkpoint, and the Edge TPU compiler. You only need to build it once.

## 2.5 (Optional) Setup for test your AI model on a x86_64 PC (later)

If you also want to run inference tests on the training PC (e.g. with a Coral USB Accelerator plugged in):

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

python3.10 -m venv .venv-3.10
.venv-3.10/bin/pip install --upgrade pip setuptools wheel
.venv-3.10/bin/pip install -r requirements-3.10.txt

mkdir -p ~/coral-wheels
wget -O ~/coral-wheels/tflite_runtime-2.5.0.post1-cp310-cp310-linux_x86_64.whl \
  "https://github.com/cappittall/pycoral_whl_4_python3.10/raw/main/tools/tflite_runtime-2.5.0.post1-cp310-cp310-linux_x86_64.whl"
wget -O ~/coral-wheels/pycoral-2.0.0-cp310-cp310-linux_x86_64.whl \
  "https://github.com/cappittall/pycoral_whl_4_python3.10/raw/main/tools/pycoral-2.0.0-cp310-cp310-linux_x86_64.whl"
.venv-3.10/bin/pip install ~/coral-wheels/tflite_runtime-2.5.0.post1-cp310-cp310-linux_x86_64.whl
.venv-3.10/bin/pip install ~/coral-wheels/pycoral-2.0.0-cp310-cp310-linux_x86_64.whl
```

---

**Previous:** [Step 1 — Raspberry Pi Setup](01-raspberry-pi-setup.md)
**Next:** [Step 3 — Create a Dataset](03-create-dataset.md)

[**Home**](../README.md)