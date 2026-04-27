import os
import json
import random
import tensorflow as tf
from PIL import Image
import io

# Konfiguration
DATASET_DIR = 'dataset'
JSON_FILES = [
    'dataset-black.json',
    'dataset-green.json',
    'dataset-orange.json',
    'dataset-red.json'
]
OUTPUT_TRAIN = 'dataset/train.record'
OUTPUT_VAL = 'dataset/val.record'
LABEL_MAP = {
    'black': 1,
    'green': 2,
    'orange': 3,
    'red': 4
}

def create_tf_example(data_item, label_map):
    # Pfad zum Bild auflösen (URL zu lokalem Pfad)
    # Beispiel: http://127.0.0.1:1000/black/frame_0000.png -> dataset/black/frame_0000.png
    url = data_item['data']['image_url']
    path_parts = url.split('/')[-2:] # Nimmt "black/frame_0000.png"
    img_path = os.path.join(DATASET_DIR, *path_parts)
    
    if not os.path.exists(img_path):
        print(f"Warnung: Bild nicht gefunden: {img_path}")
        return None

    # Bild laden für Dimensionen und Daten
    with tf.io.gfile.GFile(img_path, 'rb') as fid:
        encoded_jpg = fid.read()
    
    image = Image.open(io.BytesIO(encoded_jpg))
    width, height = image.size
    filename = os.path.basename(img_path).encode('utf8')
    image_format = b'png' # Deine Bilder sind .png

    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    classes_text = []
    classes = []

    # Bounding Boxes aus "predictions" oder "annotations" lesen
    results = []
    if 'annotations' in data_item and data_item['annotations']:
        results = data_item['annotations'][0]['result']
    elif 'predictions' in data_item and data_item['predictions']:
        results = data_item['predictions'][0]['result']

    for res in results:
        if res['type'] != 'rectanglelabels':
            continue
        
        val = res['value']
        label = val['rectanglelabels'][0]
        
        # Label Studio nutzt Prozentwerte (0-100)
        # Für TFRecord brauchen wir normalisierte Werte (0.0-1.0)
        xmin = val['x'] / 100.0
        ymin = val['y'] / 100.0
        xmax = (val['x'] + val['width']) / 100.0
        ymax = (val['y'] + val['height']) / 100.0

        xmins.append(xmin)
        xmaxs.append(xmax)
        ymins.append(ymin)
        ymaxs.append(ymax)
        classes_text.append(label.encode('utf8'))
        classes.append(label_map[label])

    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': tf.train.Feature(int64_list=tf.train.Int64List(value=[height])),
        'image/width': tf.train.Feature(int64_list=tf.train.Int64List(value=[width])),
        'image/filename': tf.train.Feature(bytes_list=tf.train.BytesList(value=[filename])),
        'image/source_id': tf.train.Feature(bytes_list=tf.train.BytesList(value=[filename])),
        'image/encoded': tf.train.Feature(bytes_list=tf.train.BytesList(value=[encoded_jpg])),
        'image/format': tf.train.Feature(bytes_list=tf.train.BytesList(value=[image_format])),
        'image/object/bbox/xmin': tf.train.Feature(float_list=tf.train.FloatList(value=xmins)),
        'image/object/bbox/xmax': tf.train.Feature(float_list=tf.train.FloatList(value=xmaxs)),
        'image/object/bbox/ymin': tf.train.Feature(float_list=tf.train.FloatList(value=ymins)),
        'image/object/bbox/ymax': tf.train.Feature(float_list=tf.train.FloatList(value=ymaxs)),
        'image/object/class/text': tf.train.Feature(bytes_list=tf.train.BytesList(value=classes_text)),
        'image/object/class/label': tf.train.Feature(int64_list=tf.train.Int64List(value=classes)),
    }))
    return tf_example

def main():
    all_items = []
    for json_file in JSON_FILES:
        with open(os.path.join(DATASET_DIR, json_file), 'r') as f:
            all_items.extend(json.load(f))
    
    random.shuffle(all_items)
    
    # 90% Training, 10% Validierung
    split = int(0.9 * len(all_items))
    train_items = all_items[:split]
    val_items = all_items[split:]

    for output_file, items in [(OUTPUT_TRAIN, train_items), (OUTPUT_VAL, val_items)]:
        writer = tf.io.TFRecordWriter(output_file)
        count = 0
        for item in items:
            example = create_tf_example(item, LABEL_MAP)
            if example:
                writer.write(example.SerializeToString())
                count += 1
        writer.close()
        print(f"Erfolgreich {count} Beispiele in {output_file} geschrieben.")

if __name__ == '__main__':
    main()
