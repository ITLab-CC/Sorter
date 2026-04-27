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
    ffmpeg \
    protobuf-compiler

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
export SPINNAKER_GENTL64_CTI=/opt/spinnaker/lib/spinnaker-gentl/Spinnaker_GenTL.cti
.venv-3.10/bin/pip install --upgrade pip
.venv-3.10/bin/pip install -r ./actuator/requirements-3.10.txt
.venv-3.10/bin/pip install -r ./sensor/requirements-3.10.txt

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
.venv-3.10/bin/pip install spinnaker_python-4.3.0.189-cp310-cp310-linux_aarch64.whl

cd ..
rm -rf spinnaker_python spinnaker_sdk

cd ..

sudo .venv-3.10/bin/python main.py
```

# Create a Dataset
1. Create a lot of pictures
First put only one color of marbles in the sorter and create a lot of pictures.It is recommended to create at least 200 pictures per marble color. You can use the following code to create a dataset of pictures. The code will save the pictures in the 'dataset/out' folder.
```py
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
mkdir label-studio
chown :0 label-studio
sudo docker run -p 8080:8080 -v $(pwd)/label-studio/dataset:/label-studio/data --name label-studio -d heartexlabs/label-studio:latest
```
Now open http://localhost:8080 in your web browser and you should see the Label Studio interface.

To import all the images you have to run a local http server which serves the dataset folder. You can do this by running the following command in the dataset folder:
```bash
sudo python3 http-server.py
```
Now you can import the images in Label Studio by uploading the json files in the dataset folder. You can do this by clicking on the 'Import' button in the Label Studio interface and selecting the json files in the dataset folder. After that you should see all the images in the Label Studio interface and you can review the labels and correct them if necessary.

![Label Studio](docs-img/LabelStudio.png)

4. Train the model
A single self-contained Docker image performs the **complete** pipeline – TFRecord generation, fine-tuning of SSD MobileNet V2, TFLite export, INT8 quantization and Edge TPU compilation – with `dataset/` as the only input and `my-models/` as the only output. The image bakes in TensorFlow 2.11, the TF Object Detection API, the pretrained checkpoint and the Edge TPU compiler.

### 4.1 Build the image (once)
```bash
sudo docker build -f Dockerfile.train -t sorter-train:latest .
```

### 4.2 Run the full pipeline
With your labeled `dataset/` populated by step 3 (containing both the per-color image folders and the `dataset-*.json` files exported from Label Studio):

```bash
mkdir -p my-models

sudo docker run --rm \
  -v "$(pwd)/dataset:/dataset" \
  -v "$(pwd)/my-models:/my-models" \
  sorter-train:latest
```

That is the entire training command. The container will, in order:

1. Generate `train.record` / `val.record` (90/10 split) into `my-models/records/`.
2. Render a container-friendly `pipeline.config` into `my-models/pipeline.config`.
3. Fine-tune SSD MobileNet V2 (`num_steps: 50000` from `pipeline.config`) – checkpoints land in `my-models/checkpoints/`.
4. Export a TFLite-friendly `saved_model/` into `my-models/tflite_export/`.
5. Quantize to INT8 using ~100 calibration images sampled from `/dataset`, producing `my-models/ssd_mobilenet_v2_quant.tflite`.
6. Compile for the Edge TPU, producing `my-models/ssd_mobilenet_v2_quant_edgetpu.tflite`.

When it finishes you will find in `my-models/`:

- `marbel_coral.tflite` – the Edge TPU model (use this with `test_coral.py` / `main.py`).
- `ssd_mobilenet_v2_quant.tflite` – the INT8 CPU fallback.
- `tflite_export/saved_model/` – pre-quantization SavedModel.
- `checkpoints/` – training checkpoints + TensorBoard event files.
- `labels.txt` – id-to-name map matching `label_map.pbtxt`.

> **GPU acceleration:** if the host has the NVIDIA Container Toolkit installed, append `--gpus all` to the `docker run` command above. Without it everything still works, just on CPU.

> **Quick smoke test:** to sanity-check the pipeline without waiting for 50 000 training steps, edit `num_steps` in `pipeline.config` (e.g. to `1000`) and rebuild the image.

### 4.3 Inspect intermediate steps (optional)
The image's entrypoint is `sorter-train`, but you can override it to run individual stages, e.g.:

```bash
# Drop into a shell inside the image
sudo docker run --rm -it \
  -v "$(pwd)/dataset:/dataset" \
  -v "$(pwd)/my-models:/my-models" \
  --entrypoint bash sorter-train:latest

# Re-run only the Edge TPU compile step
sudo docker run --rm \
  -v "$(pwd)/my-models:/my-models" \
  --entrypoint edgetpu_compiler sorter-train:latest \
  -o /my-models /my-models/ssd_mobilenet_v2_quant.tflite
```

### 4.4 (Optional) Native pyenv path without Docker
If you prefer not to use Docker, the same workflow runs natively under Python 3.9:

```bash
python3.9 -m venv .venv-3.9
.venv-3.9/bin/pip install --upgrade pip
.venv-3.9/bin/pip install -r requirements-3.9.txt

# Object Detection API
git clone https://github.com/tensorflow/models.git   # skip if already present
cd models/research
protoc object_detection/protos/*.proto --python_out=.
cp object_detection/packages/tf2/setup.py .
cd ../../
.venv-3.9/bin/python -m pip install ./models/research/

# Pretrained checkpoint
mkdir -p models/pretrained
curl -L http://download.tensorflow.org/models/object_detection/tf2/20200711/ssd_mobilenet_v2_320x320_coco17_tpu-8.tar.gz \
  | tar -xz -C models/pretrained

# TFRecords + training (writes records to dataset/)
sudo .venv-3.9/bin/python convert_dataset.py
sudo .venv-3.9/bin/python models/research/object_detection/model_main_tf2.py \
  --pipeline_config_path=pipeline.config --model_dir=my-models --alsologtostderr

# Export + quantize
.venv-3.9/bin/python models/research/object_detection/export_tflite_graph_tf2.py \
  --pipeline_config_path pipeline.config \
  --trained_checkpoint_dir my-models \
  --output_directory my-models/tflite_export
.venv-3.9/bin/python docker/quantize.py \
  --saved-model my-models/tflite_export/saved_model \
  --dataset-dir dataset \
  --out my-models/ssd_mobilenet_v2_quant.tflite
```

The `edgetpu_compiler` itself is only available via Google's APT repo. Install it on Debian with:

```bash
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/coral-edgetpu-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/coral-edgetpu-archive-keyring.gpg] https://packages.cloud.google.com/apt coral-edgetpu-stable main" \
  | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
sudo apt-get update && sudo apt-get install -y edgetpu-compiler

edgetpu_compiler -o my-models my-models/ssd_mobilenet_v2_quant.tflite
cp my-models/ssd_mobilenet_v2_quant_edgetpu.tflite marbel_coral.tflite
```

### 4.5 Smoke-test the compiled model on the Coral USB Accelerator
With the accelerator plugged in:

```bash
sudo .venv-3.10/bin/python test_coral.py \
  --model my-models/marbel_coral.tflite \
  --labels my-models/labels.txt \
  --image dataset/red/frame_0000.png
```

Typical inference time on the Edge TPU is ~20 ms per frame.

## Sources
- **Model:** [SSD MobileNet V2 320x320 (COCO17 TPU-8)](http://download.tensorflow.org/models/object_detection/tf2/20200711/ssd_mobilenet_v2_320x320_coco17_tpu-8.tar.gz)
- **Framework:** [TensorFlow Object Detection API](https://github.com/tensorflow/models/tree/master/research/object_detection)
- **Edge TPU compiler:** [coral.ai/docs/edgetpu/compiler](https://coral.ai/docs/edgetpu/compiler/)

5. Run the model
Now you have a trained model and you can use it to sort the marbles. Place `marbel_coral.tflite` and `labels.txt` next to `main.py` and start the full sorter:

```bash
sudo .venv-3.10/bin/python main.py
```

Enjoy your sorted marbles!