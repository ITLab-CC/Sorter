"""Convert a SavedModel to an INT8-quantized TFLite model.

Uses a representative dataset sampled from the per-color image folders so
the resulting graph is suitable for the Edge TPU compiler.
"""

import argparse
from pathlib import Path

import tensorflow as tf


def make_representative_dataset(dataset_dir: Path, num_samples: int):
    image_files = sorted(dataset_dir.rglob("*.png"))
    if not image_files:
        raise SystemExit(f"No PNG images found under {dataset_dir}")
    image_files = image_files[:num_samples]

    def gen():
        for img_path in image_files:
            img = tf.io.read_file(str(img_path))
            img = tf.image.decode_image(img, channels=3, expand_animations=False)
            img = tf.image.resize(img, [300, 300])
            img = tf.cast(img, tf.float32) / 127.5 - 1.0  # MobileNet V2 scaling
            yield [tf.expand_dims(img, axis=0)]

    return gen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--saved-model", required=True,
                        help="Path to the saved_model/ directory produced by export_tflite_graph_tf2.py.")
    parser.add_argument("--dataset-dir", required=True,
                        help="Directory containing the calibration images (PNGs are sampled recursively).")
    parser.add_argument("--out", required=True, help="Output .tflite path.")
    parser.add_argument("--num-samples", type=int, default=100,
                        help="Number of images to use for calibration (default: 100).")
    args = parser.parse_args()

    converter = tf.lite.TFLiteConverter.from_saved_model(args.saved_model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = make_representative_dataset(
        Path(args.dataset_dir), args.num_samples
    )
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.uint8
    converter.inference_output_type = tf.float32

    tflite_model = converter.convert()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(tflite_model)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
