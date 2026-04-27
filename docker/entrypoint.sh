#!/usr/bin/env bash
# End-to-end pipeline: TFRecords -> training -> TFLite export -> INT8 -> Edge TPU.
# Inputs (mounted volumes):
#   /dataset      -- the labeled dataset (dataset-*.json + per-color image folders)
# Outputs (mounted volume):
#   /my-models    -- all artifacts, including the final marbel_coral.tflite
set -euo pipefail

DATASET_DIR="${DATASET_DIR:-/dataset}"
OUT_DIR="${OUT_DIR:-/my-models}"
ASSETS=/opt/sorter
OD_API=/opt/models

if [[ ! -d "$DATASET_DIR" ]]; then
  echo "ERROR: dataset directory $DATASET_DIR not found. Mount it with -v <host>:/dataset" >&2
  exit 1
fi
mkdir -p "$OUT_DIR"

RECORDS_DIR="$OUT_DIR/records"
CKPT_DIR="$OUT_DIR/checkpoints"
EXPORT_DIR="$OUT_DIR/tflite_export"
PIPELINE="$OUT_DIR/pipeline.config"

mkdir -p "$RECORDS_DIR" "$CKPT_DIR" "$EXPORT_DIR"

echo "==> [1/6] Building TFRecords from $DATASET_DIR"
python3 "$ASSETS/build_tfrecords.py" \
  --dataset-dir "$DATASET_DIR" \
  --train-out "$RECORDS_DIR/train.record" \
  --val-out "$RECORDS_DIR/val.record"

echo "==> [2/6] Rendering pipeline.config with container paths"
sed \
  -e "s|dataset/train\.record|$RECORDS_DIR/train.record|g" \
  -e "s|dataset/val\.record|$RECORDS_DIR/val.record|g" \
  -e "s|label_map\.pbtxt|$ASSETS/label_map.pbtxt|g" \
  -e "s|models/pretrained/ssd_mobilenet_v2_320x320_coco17_tpu-8/checkpoint/ckpt-0|$ASSETS/pretrained/ssd_mobilenet_v2_320x320_coco17_tpu-8/checkpoint/ckpt-0|g" \
  "$ASSETS/pipeline.config" > "$PIPELINE"

echo "==> [3/6] Training (this is the long step)"
python3 "$OD_API/research/object_detection/model_main_tf2.py" \
  --pipeline_config_path="$PIPELINE" \
  --model_dir="$CKPT_DIR" \
  --alsologtostderr

echo "==> [4/6] Exporting TFLite-friendly graph"
python3 "$OD_API/research/object_detection/export_tflite_graph_tf2.py" \
  --pipeline_config_path "$PIPELINE" \
  --trained_checkpoint_dir "$CKPT_DIR" \
  --output_directory "$EXPORT_DIR"

echo "==> [5/6] Quantizing to INT8 TFLite"
python3 "$ASSETS/quantize.py" \
  --saved-model "$EXPORT_DIR/saved_model" \
  --dataset-dir "$DATASET_DIR" \
  --out "$OUT_DIR/ssd_mobilenet_v2_quant.tflite"

echo "==> [6/6] Compiling for Edge TPU"
edgetpu_compiler -o "$OUT_DIR" "$OUT_DIR/ssd_mobilenet_v2_quant.tflite"

cp "$OUT_DIR/ssd_mobilenet_v2_quant_edgetpu.tflite" "$OUT_DIR/marbel_coral.tflite"
cat > "$OUT_DIR/labels.txt" <<'EOF'
1 black
2 green
3 orange
4 red
EOF

echo
echo "Done. Final artifacts in $OUT_DIR:"
echo "  - marbel_coral.tflite             (Edge TPU model, use this with test_coral.py / main.py)"
echo "  - ssd_mobilenet_v2_quant.tflite   (INT8 CPU model)"
echo "  - tflite_export/saved_model/      (pre-quantization SavedModel)"
echo "  - checkpoints/                    (training checkpoints + tensorboard events)"
echo "  - labels.txt                      (id-to-name map)"
