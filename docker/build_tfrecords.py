"""Convert Label Studio JSON exports to TFRecord files.

This is a parameterized version of `convert_dataset.py` that reads its
inputs and writes its outputs to paths supplied on the command line, so
it is suitable for use inside the training Docker image where the
dataset directory and the output directory are mounted volumes.
"""

import argparse
import io
import json
import os
import random
import re
import sys

import tensorflow as tf
from PIL import Image


def parse_label_map(path):
    """Parse a label_map.pbtxt file and return a ``{name: id}`` dict."""
    text = open(path).read()
    label_map = {}
    for block in re.finditer(r'item\s*\{(.*?)\}', text, re.DOTALL):
        body = block.group(1)
        id_match = re.search(r'id:\s*(\d+)', body)
        name_match = re.search(r"name:\s*'([^']+)'", body)
        if id_match and name_match:
            label_map[name_match.group(1)] = int(id_match.group(1))
    return label_map


def create_tf_example(data_item, dataset_dir, label_map):
    url = data_item["data"]["image"]
    # e.g. http://127.0.0.1:1000/black/frame_0000.png -> <dataset_dir>/black/frame_0000.png
    path_parts = url.split("/")[-2:]
    img_path = os.path.join(dataset_dir, *path_parts)

    if not os.path.exists(img_path):
        print(f"Warning: image not found: {img_path}", file=sys.stderr)
        return None

    with tf.io.gfile.GFile(img_path, "rb") as fid:
        encoded = fid.read()

    image = Image.open(io.BytesIO(encoded))
    width, height = image.size
    filename = os.path.basename(img_path).encode("utf8")
    image_format = b"png"

    xmins, xmaxs, ymins, ymaxs = [], [], [], []
    classes_text, classes = [], []

    results = []
    if data_item.get("annotations"):
        results = data_item["annotations"][0]["result"]
    elif data_item.get("predictions"):
        results = data_item["predictions"][0]["result"]

    for res in results:
        if res["type"] != "rectanglelabels":
            continue
        val = res["value"]
        label = val["rectanglelabels"][0]
        xmins.append(val["x"] / 100.0)
        ymins.append(val["y"] / 100.0)
        xmaxs.append((val["x"] + val["width"]) / 100.0)
        ymaxs.append((val["y"] + val["height"]) / 100.0)
        classes_text.append(label.encode("utf8"))
        classes.append(label_map[label])

    return tf.train.Example(features=tf.train.Features(feature={
        "image/height": tf.train.Feature(int64_list=tf.train.Int64List(value=[height])),
        "image/width": tf.train.Feature(int64_list=tf.train.Int64List(value=[width])),
        "image/filename": tf.train.Feature(bytes_list=tf.train.BytesList(value=[filename])),
        "image/source_id": tf.train.Feature(bytes_list=tf.train.BytesList(value=[filename])),
        "image/encoded": tf.train.Feature(bytes_list=tf.train.BytesList(value=[encoded])),
        "image/format": tf.train.Feature(bytes_list=tf.train.BytesList(value=[image_format])),
        "image/object/bbox/xmin": tf.train.Feature(float_list=tf.train.FloatList(value=xmins)),
        "image/object/bbox/xmax": tf.train.Feature(float_list=tf.train.FloatList(value=xmaxs)),
        "image/object/bbox/ymin": tf.train.Feature(float_list=tf.train.FloatList(value=ymins)),
        "image/object/bbox/ymax": tf.train.Feature(float_list=tf.train.FloatList(value=ymaxs)),
        "image/object/class/text": tf.train.Feature(bytes_list=tf.train.BytesList(value=classes_text)),
        "image/object/class/label": tf.train.Feature(int64_list=tf.train.Int64List(value=classes)),
    }))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", required=True,
                        help="Directory containing dataset-*.json and the per-color image folders.")
    parser.add_argument("--label-map", required=True,
                        help="Path to label_map.pbtxt.")
    parser.add_argument("--train-out", required=True, help="Path of train.record to write.")
    parser.add_argument("--val-out", required=True, help="Path of val.record to write.")
    parser.add_argument("--val-split", type=float, default=0.1,
                        help="Fraction of items used for validation (default: 0.1).")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    label_map = parse_label_map(args.label_map)
    if not label_map:
        sys.exit(f"No labels found in {args.label_map}")
    print(f"Labels from {args.label_map}: {label_map}")

    json_files = [f"dataset-{name}.json" for name in sorted(label_map.keys())]

    random.seed(args.seed)

    all_items = []
    for json_file in json_files:
        path = os.path.join(args.dataset_dir, json_file)
        if not os.path.exists(path):
            print(f"Warning: {path} not found, skipping.", file=sys.stderr)
            continue
        with open(path, "r") as f:
            all_items.extend(json.load(f))

    if not all_items:
        sys.exit(f"No items found in {args.dataset_dir}. "
                 f"Expected one or more of: {json_files}")

    random.shuffle(all_items)
    split = int((1.0 - args.val_split) * len(all_items))
    train_items = all_items[:split]
    val_items = all_items[split:]

    for output_file, items in [(args.train_out, train_items), (args.val_out, val_items)]:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        writer = tf.io.TFRecordWriter(output_file)
        count = 0
        for item in items:
            example = create_tf_example(item, args.dataset_dir, label_map)
            if example is not None:
                writer.write(example.SerializeToString())
                count += 1
        writer.close()
        print(f"Wrote {count} examples to {output_file}")


if __name__ == "__main__":
    main()
