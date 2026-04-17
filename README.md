
# Python

## Python 3.10

#### Install dependcy
```bash
sudo apt install -y build-essential \
libssl-dev libffi-dev libbz2-dev \
libreadline-dev libsqlite3-dev \
libncursesw5-dev libgdbm-dev libc6-dev \
liblzma-dev tk-dev libnss3-dev \
zlib1g-dev uuid-dev libxml2-dev \
libxmlsec1-dev libncurses5-dev \
wget
```

#### Download Python

wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz

#### Unpack downloaded file

```bash
tar -xf Python-3.10.0.tgz
```

#### Configure the build process

```bash
cd Python-3.10.0
./configure --enable-optimizations --with-ensurepip=install
```
#### Compile Python

```bash
make -j$(nproc)
```

#### Install compilet python version

```bash
sudo make altinstall
```



## Python 3.9

```bash
sudo apt install -y build-essential \
libssl-dev libffi-dev libbz2-dev \
libreadline-dev libsqlite3-dev \
libncursesw5-dev libgdbm-dev libc6-dev \
liblzma-dev tk-dev libnss3-dev \
zlib1g-dev uuid-dev libxml2-dev \
libxmlsec1-dev libncurses5-dev \
wget
```

#### Download Python

wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz

#### Unpack downloaded file

```bash
tar -xf Python-3.9.18.tgz
```

#### Configure the build process

```bash
cd Python-3.9.18.tgz
./configure --enable-optimizations --with-ensurepip=install
```
#### Compile Python

```bash
make -j$(nproc)
```

#### Install compilet python

```bash
sudo make altinstall
```


## Camera
1. Create venv and install dependencies
```
python3.10 -m venv .venv-3.10
source .venv-3.10/bin/activate
export SPINNAKER_GENTL64_CTI=/opt/spinnaker/lib/spinnaker-gentl/Spinnaker_GenTL.cti
cd camera
pip3 install -r requirements.txt
cd ..
```

2. Downloade the python and the sdk version of the Spinnaker SDK from the following link: 
https://www.teledynevisionsolutions.com/support/support-center/software-firmware-downloads/iis/spinnaker-sdk-download/spinnaker-sdk--download-files/?pn=Spinnaker+SDK&vn=Spinnaker+SDK
There should be two files:
- 'spinnaker-4.0.0.116-arm64-pkg-22.04.tar.gz'
- 'spinnaker_python-4.0.0.116-cp310-cp310-linux_aarch64.tar.gz'

3. unpacke:
```bash
mkdir spinnaker_sdk spinnaker_python
tar -xzvf spinnaker-4.0.0.116-arm64-pkg-22.04.tar.gz -C spinnaker_sdk
tar -xzvf spinnaker_python-4.0.0.116-cp310-cp310-linux_aarch64.tar.gz -C spinnaker_python
```

4. install:
```bash
cd spinnaker_sdk/spinnaker-4.0.0.116-arm64 
./install_spinnaker_arm.sh

cd ../../spinnaker_python
pip3 install spinnaker_python-4.0.0.116-cp310-cp310-linux_aarch64.whl
cd ..
rm -rf spinnaker_python spinnaker_sdk
```

5. Run it
```bash
cd camera
python3 main.py
```


# Dev

We are using mypy. To install it, run:
```bash
pip3 install mypy
```

To check the types, run:
```bash
python3 -m mypy .
```
