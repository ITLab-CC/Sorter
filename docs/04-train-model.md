# Step 4 — Train the Model

A single Docker container performs the complete training pipeline — TFRecord generation, SSD MobileNet V2 fine-tuning, TFLite export, INT8 quantization, and Edge TPU compilation.

> **Machine:** Training PC with NVIDIA GPU
> Make sure you have completed [Step 2 — Training PC Setup](02-training-pc-setup.md) first.

## 4.1 Copy the dataset to the training PC

Transfer the `dataset/` folder (with both the per-color image folders **and** the `dataset-*.json` files from Label Studio) to the project root on your training PC.

## 4.2 Run the full training pipeline

```bash
sudo docker build -f Dockerfile.train -t sorter-train:latest .
```

```bash
mkdir -p my-models

sudo docker run --rm \
  -v "$(pwd)/dataset:/dataset" \
  -v "$(pwd)/my-models:/my-models" \
  --gpus all \
  sorter-train:latest
```

The container will, in order:

1. Generate `train.record` / `val.record` (90/10 split) into `my-models/records/`.
2. Render a container-friendly `pipeline.config` into `my-models/pipeline.config`.
3. Fine-tune SSD MobileNet V2 (`num_steps: 50000`) — checkpoints land in `my-models/checkpoints/`.
4. Export a TFLite-friendly `saved_model/` into `my-models/tflite_export/`.
5. Quantize to INT8 using ~100 calibration images from the dataset, producing `my-models/ssd_mobilenet_v2_quant.tflite`.
6. Compile for the Edge TPU, producing `my-models/ssd_mobilenet_v2_quant_edgetpu.tflite`.

## 4.3 Output files

When training finishes you will find in `my-models/`:

| File | Description |
|---|---|
| `marbel_coral.tflite` | Edge TPU model — use this on the Raspberry Pi |
| `ssd_mobilenet_v2_quant.tflite` | INT8 CPU fallback |
| `tflite_export/saved_model/` | Pre-quantization SavedModel |
| `checkpoints/` | Training checkpoints + TensorBoard event files |
| `labels.txt` | Class id-to-name map matching `label_map.pbtxt` |

## 4.4 Quick smoke test

To sanity-check the pipeline without waiting for 50 000 steps, edit `num_steps` in `pipeline.config` (e.g. to `1000`) and rebuild the image.

```bash
sudo docker build -f Dockerfile.train -t sorter-train:latest .
```

## 4.5 Test on the Coral USB Accelerator

With the coral plugged in you can also test the compiled model on the training PC, not only on the Raspberry Pi. This is a good way to verify that the model works before deploying it.

```bash
sudo .venv-3.10/bin/python test_coral.py \
  --model my-models/marbel_coral.tflite \
  --labels my-models/labels.txt \
  --image dataset/red/frame_0000.png
```

To classify all images in `dataset/mixed-not-labeled/` at once:

```bash
sudo .venv-3.10/bin/python classify_mixed.py
```

Typical inference time on the Edge TPU is ~6 ms per frame.

---

**Previous:** [Step 3 — Create a Dataset](03-create-dataset.md)
**Next:** [Step 5 — Run the Sorter](05-run-sorter.md)

[**Home**](../README.md)