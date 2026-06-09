# Step 5 — Run the Sorter

You now have a trained Edge TPU model. Time to sort some marbles.

> **Machine:** Raspberry Pi

## 5.1 Copy the model to the Raspberry Pi

Transfer `my-models/marbel_coral.tflite` and `my-models/labels.txt` from the training PC to the Raspberry Pi project directory (inside `my-models/`).

## 5.2 Start the sorter

Make sure the camera, Coral USB Accelerator, motors, and sensors are all connected, then run:

```bash
sudo .venv-3.10/bin/python main.py
```

Enjoy your sorted marbles!

---

**Previous:** [Step 4 — Train the Model](04-train-model.md)
**Back to:** [README](../README.md)

[**Home**](../README.md)