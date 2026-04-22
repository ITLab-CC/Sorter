# AI-Sorter
This is a project for sorting marbles using AI. The project is divided into three main modules: the Sensor module, the Actuator module and the AI module. The Sensor module is responsible for collecting data from the sorter, the Actuator module is responsible for controlling the physical components of the system, and the AI module is responsible for processing the data and making decisions based on it.

## Installation Docker
TODO

## Installation
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

LINE1='export PYENV_ROOT="$HOME/.pyenv"'
LINE2='command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
LINE3='eval "$(pyenv init -)"'
grep -qF "$LINE1" ~/.bashrc || echo "$LINE1" >> ~/.bashrc
grep -qF "$LINE2" ~/.bashrc || echo "$LINE2" >> ~/.bashrc
grep -qF "$LINE3" ~/.bashrc || echo "$LINE3" >> ~/.bashrc
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

pyenv install 3.9.25
pyenv install 3.10.20

pyenv local 3.10.20 3.9.25


python3.10 -m venv .venv-3.10
source .venv-3.10/bin/activate
export SPINNAKER_GENTL64_CTI=/opt/spinnaker/lib/spinnaker-gentl/Spinnaker_GenTL.cti
pip install --upgrade pip
pip install -r ./actuator/requirements-3.10.txt
pip install -r ./sensor/requirements-3.10.txt

cd sensor
```

Downloade the python and the sdk version of the Spinnaker SDK from the following link to the sensor folder: 

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
```

```bash
cd ../../spinnaker_python
pip3 install spinnaker_python-4.3.0.189-cp310-cp310-linux_aarch64.whl

cd ..
rm -rf spinnaker_python spinnaker_sdk

cd ..

sudo .venv-3.10/bin/python main.py
```

# Create a Dataset
1. Create a lot of pictures
First put only one color of marbles in the sorter and create a lot of pictures.It is recommended to create at least 200 pictures per marble color. You can use the following code to create a dataset of pictures. The code will save the pictures in the 'dataset/out' folder.
```py
source .venv-3.10/bin/activate
sudo .venv-3.10/bin/python create_unlabeled_dataset.py
```

After that you should have a lot of pictures in the 'dataset/out' folder which all have the same color of marbles. Now rename the out folder to the color of the marbles you used by doing the following command:
```bash
mv dataset/out dataset/red
mkdir -p dataset/out
```

Now replace all marbels with the next color. You can use the following command to move the elevator motor up to make it easier to change the marbles:
```bash
sudo .venv-3.10/bin/python actuator/elevator_motor.py
```

Now repeat the process until you have a folder for each color of marbles. You should end up with a dataset folder that looks like this:
```bash
dataset
├── black
│   ├── frame_0000.png
│   ├── frame_0001.png
│   └── ...
├── orange
│   ├── frame_0000.png
│   ├── frame_0001.png
│   └── ...
├── green
│   ├── frame_0000.png
│   ├── frame_0001.png
│   └── ...
├── red
│   ├── frame_0000.png
│   ├── frame_0001.png
│   └── ...
└── ...
```

2. Label the pictures
Now you have a lot of pictures of marbles but they are not labeled. You can use the following script to label the pictures automatically. It uses openCV to detect the marbles in the pictures. But its not perfect and you should check the labels and correct them if necessary. The script will save for each folder of pictures as dataset-[color].json files in the dataset folder. These files contain the labels for each picture in the corresponding folder.
```py
sudo .venv-3.10/bin/python label_dataset.py
```

3. Review the labels
Now you have a lot of labeled pictures but the labels are not perfect. You can use the following tool to review the labels and correct them if necessary. The tool is called Label Studio and it is a web-based tool for labeling data. You can use it to review the labels and correct them if necessary. The tool will save the corrected labels in the same dataset-[color].json files in the dataset folder. To start Label Studio, run the following command:
```bash
curl -sSL https://get.docker.com | sh
docker run -p 8080:8080 -v $(pwd)/dataset:/label-studio/data --name label-studio heartexlabs/label-studio:latest
```
Now open http://localhost:8080 in your web browser and you should see the Label Studio interface.

To import all the images you have to run a local http server which serves the dataset folder. You can do this by running the following command in the dataset folder:
```bash
sudo python3 http-server.py
```
Now you can import the images in Label Studio by uploading the json files in the dataset folder. You can do this by clicking on the 'Import' button in the Label Studio interface and selecting the json files in the dataset folder. After that you should see all the images in the Label Studio interface and you can review the labels and correct them if necessary.

![Label Studio](docs-img/LabelStudio.png)

4. Train the model
Now you have a lot of labeled pictures and you can use them to train the model.

TODO

5. Run the model
Now you have a trained model and you can use it to sort the marbles. You have to save the model into the `models` folder. You can start the model with the full sorter by running the following command:
```bash
sudo .venv-3.10/bin/python main.py
```

Enjoy your sorted marbles!