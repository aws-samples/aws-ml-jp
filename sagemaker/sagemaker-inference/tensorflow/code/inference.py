import json, numpy as np, tensorflow as tf, base64, os
from pathlib import Path

INPUT_SIZE=(224,224)

with open('/opt/ml/model/code/labels.txt','rt') as f:
    label = f.read().split('\n')[0:-1]

def input_handler(data, context):
    b64_data = json.loads(data.read().decode("utf-8"))['b64_image']
    raw_tensor = tf.io.decode_jpeg(base64.b64decode(b64_data.encode('utf-8')))
    normalization_list = ((tf.image.resize(raw_tensor,(INPUT_SIZE[0],INPUT_SIZE[1])).numpy()-127.5)/127.5).reshape(-1,INPUT_SIZE[0],INPUT_SIZE[1],3).tolist()
    return json.dumps({"instances":normalization_list})
    
def output_handler(data, context):
    response_content_type = context.accept_header
    prediction = label[np.argmax(json.loads(data.content.decode('utf-8'))['predictions'][0])]
    return prediction, response_content_type
