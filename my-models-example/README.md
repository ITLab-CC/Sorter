# Pretrained Model (ready to use)

This folder contains a **pretrained, ready-to-use** marble-sorting model so you
can run the sorter **without training your own**.

If you don't have an NVIDIA GPU / training PC, or you just want to try the
sorter quickly, use the files in this folder instead of completing
[Step 4 — Train the Model](../docs/04-train-model.md).

## Contents

| File | Description |
|---|---|
| `marbel_coral.tflite` | Edge TPU model — runs on the Coral USB Accelerator |
| `labels.txt` | Class id-to-name map (must match `label_map.pbtxt`) |

The model is an SSD MobileNet V2 detector, quantized to INT8 and compiled for
the Coral Edge TPU.

### Classes (`labels.txt`)

```
0 black
1 green
2 orange
3 red
```

## How to use it

The sorter loads its model from `my-models/` (which is **not** tracked by git,
see `.gitignore`). Copy this folder's contents into `my-models/`:

```bash
# From the project root, on the Raspberry Pi
mkdir -p my-models
cp my-models-example/marbel_coral.tflite my-models-example/labels.txt my-models/
```

Then run the sorter as usual:

```bash
sudo .venv-3.10/bin/python main.py
```

> Want better accuracy for your own marbles/lighting? Train your own model by
> following [Step 4 — Train the Model](../docs/04-train-model.md) and place the
> output in `my-models/` instead.
