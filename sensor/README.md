# Information about the Actuator module.
This folder contains the code for the Sensors. The sensors are responsible for collecting data from the sorter. It includes code for:
- FLIR camera (500FPS)
- Light beam sensor

# Installation

## Docker
Downloade the python and the sdk version of the Spinnaker SDK from the following link: 

https://www.teledynevisionsolutions.com/support/support-center/software-firmware-downloads/iis/spinnaker-sdk-download/spinnaker-sdk--download-files/?pn=Spinnaker+SDK&vn=Spinnaker+SDK

There should be two files:
- For x64 (PCs):
- - (Linux Ubuntu 22.04 -- 64-bit) 'spinnaker-4.3.0.189-Ubuntu22.04-amd64-pkg.tar.gz'
- - (Linux Ubuntu 22.04 -- 64-bit Python 3.10) 'spinnaker_python-4.3.0.189-cp310-cp310-linux_x86_64.tar.gz'

```bash
sudo docker build -t sorter-actuator .
sudo docker run -it --rm \
    --privileged \
    -v /dev/bus/usb:/dev/bus/usb \
    -v $(pwd)/out:/out \
    --shm-size=2g \
    sorter-actuator
```

## DEV
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
    ffmpeg

curl https://pyenv.run | bash

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

pyenv install 3.10.20

pyenv local 3.10.20
```

```bash
python3.10 -m venv .venv-3.10
source .venv-3.10/bin/activate
export SPINNAKER_GENTL64_CTI=/opt/spinnaker/lib/spinnaker-gentl/Spinnaker_GenTL.cti
pip install -r requirements-3.10.txt
```
---

Downloade the python and the sdk version of the Spinnaker SDK from the following link: 

https://www.teledynevisionsolutions.com/support/support-center/software-firmware-downloads/iis/spinnaker-sdk-download/spinnaker-sdk--download-files/?pn=Spinnaker+SDK&vn=Spinnaker+SDK

There should be two files:
- For ARM (Raspberry PIs):
- - (Linux Ubuntu 22.04 --ARM64) 'spinnaker-4.3.0.189-Ubuntu22.04-arm64-pkg.tar.gz'
- - (Linux Ubuntu 22.04 -- ARM64 Python 3.10) 'spinnaker_python-4.3.0.189-cp310-cp310-linux_aarch64.tar.gz'

```bash
mkdir -p spinnaker_sdk spinnaker_python
tar -xzvf spinnaker-4.3.0.189-Ubuntu22.04-arm64-pkg.tar.gz -C spinnaker_sdk
tar -xzvf spinnaker_python-4.3.0.189-cp310-cp310-linux_aarch64.tar.gz -C spinnaker_python

cd spinnaker_sdk/spinnaker-4.3.0.189-arm64/
./install_spinnaker_arm.sh

cd ../../spinnaker_python
pip3 install spinnaker_python-4.3.0.189-cp310-cp310-linux_aarch64.whl

cd ..
rm -rf spinnaker_python spinnaker_sdk
```

---

- For x64 (PCs):
- - (Linux Ubuntu 22.04 -- 64-bit) 'spinnaker-4.3.0.189-Ubuntu22.04-amd64-pkg.tar.gz'
- - (Linux Ubuntu 22.04 -- 64-bit Python 3.10) 'spinnaker_python-4.3.0.189-cp310-cp310-linux_x86_64.tar.gz'

```bash
mkdir -p spinnaker_sdk spinnaker_python
tar -xzvf spinnaker-4.3.0.189-Ubuntu22.04-amd64-pkg.tar.gz -C spinnaker_sdk
tar -xzvf spinnaker_python-4.3.0.189-cp310-cp310-linux_x86_64.tar.gz -C spinnaker_python

cd spinnaker_sdk/spinnaker-4.3.0.189-amd64/
./install_spinnaker.sh

cd ../../spinnaker_python
pip3 install spinnaker_python-4.3.0.189-cp310-cp310-linux_x86_64.whl

cd ..
rm -rf spinnaker_python spinnaker_sdk
```

# Usage

```bash
sudo .venv-3.10/bin/python [script].py
```