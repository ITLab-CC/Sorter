# AI-Sorter

An AI-powered marble sorting machine. A camera detects falling marbles, a neural network classifies them by color, and a solenoid actuator sorts them into the correct bin — all in real time on a Raspberry Pi with a Coral Edge TPU.

## What You Need

This project requires **two machines**:

### Raspberry Pi (runs the sorter)

| Component | Description |
|---|---|
| **Raspberry Pi** | Runs the sorting software (tested on Pi 4/5, Ubuntu 22.04 ARM64) |
| **FLIR Machine Vision Camera** | Captures images of marbles (uses the Spinnaker SDK) |
| **Coral USB Accelerator** | Runs the trained model for real-time inference (~6 ms/frame) |
| **Elevator motor** | Feeds marbles into the sorting area |
| **Solenoid actuator** | Diverts marbles into the correct bin |
| **NeoPixel LED strip** | Illuminates the sorting area for consistent images |
| **Light-beam sensor** | Detects when a marble passes through |

### Training PC (trains the AI model)

| Component | Description |
|---|---|
| **PC with NVIDIA GPU** | Trains the SSD MobileNet V2 model (fine-tuning ~50 000 steps) |
| **Docker + NVIDIA Container Toolkit** | The training pipeline runs inside a Docker container with GPU access |

> The training PC can be a local desktop, a cloud VM (AWS EC2, Google Cloud, etc.), or Google Colab. **Do not attempt training on the Raspberry Pi.**

## Step-by-Step Guide

Follow the guides below in order:

| Step | Guide | Machine |
|---|---|---|
| 0 | [Build the Sorter](docs/00-build-the-sorter.md) *(TODO)* | Workbench |
| 1 | [Raspberry Pi Setup](docs/01-raspberry-pi-setup.md) | Raspberry Pi |
| 2 | [Training PC Setup](docs/02-training-pc-setup.md) | Training PC |
| 3 | [Create a Dataset](docs/03-create-dataset.md) | Raspberry Pi |
| 4 | [Train the Model](docs/04-train-model.md) | Training PC |
| 5 | [Run the Sorter](docs/05-run-sorter.md) | Raspberry Pi |

## Project Structure

```
.
├── actuator/          # Motor, solenoid and LED control
├── sensor/            # Camera and light-beam sensor
├── dataset/           # Training images (created in step 3)
├── my-models/         # Trained models (created in step 4)
├── docs/              # Step-by-step setup guides
├── create_unlabeled_dataset.py
├── label_dataset.py
├── label_map.pbtxt    # Single source of truth for class labels
├── main.py            # Entry point for the sorter
├── Dockerfile.train   # Docker image for training
└── pipeline.config    # SSD MobileNet V2 training config
```

## Label Map (`label_map.pbtxt`)

`label_map.pbtxt` is the **single source of truth** for all class labels used throughout the project. Every script — labeling, TFRecord generation, training, and inference — reads its labels from this file. Never hardcode label names or IDs elsewhere.

The file uses the [TensorFlow Object Detection API label map format](https://github.com/tensorflow/models/blob/master/research/object_detection/data/kitti_label_map.pbtxt). Each class gets an `item` block with a unique `id` (starting at 1) and a `name`:

```protobuf
item {
  id: 1
  name: 'black'
}

item {
  id: 2
  name: 'green'
}

item {
  id: 3
  name: 'orange'
}

item {
  id: 4
  name: 'red'
}

```

To add or change marble colors:

1. Edit `label_map.pbtxt` — add, remove, or rename entries.
2. Make sure a matching `dataset/<name>/` folder with images exists for each label (see [Step 3](docs/03-create-dataset.md)).
3. Update `num_classes` in `pipeline.config` to match the number of items in `label_map.pbtxt`.
4. Re-run the labeling and training pipeline as usual — all scripts pick up the changes automatically.

## Sources

- **Model:** [SSD MobileNet V2 320x320 (COCO17 TPU-8)](http://download.tensorflow.org/models/object_detection/tf2/20200711/ssd_mobilenet_v2_320x320_coco17_tpu-8.tar.gz)
- **Framework:** [TensorFlow Object Detection API](https://github.com/tensorflow/models/tree/master/research/object_detection)
- **Edge TPU compiler:** [coral.ai/docs/edgetpu/compiler](https://coral.ai/docs/edgetpu/compiler/)