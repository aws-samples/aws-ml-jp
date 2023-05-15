
import numpy as np
import cv2
import sys
import random
import dlr
import time
import json
import os
from PIL import Image

os.environ['TVM_TENSORRT_CACHE_DIR'] = './cache/'
os.environ['TVM_TENSORRT_USE_FP16'] = '1'

class Inference(object):
    def __init__(self):
        self.log_file = '/tmp/Greengrass_HelloWorld.log'

    def transform(self, img):
        # Normalize
        image = img / 127.5
        image -= 1.
    
        # Transpose
        if len(image.shape) == 2:  # for greyscale image
            image = np.expand_dims(image, axis=2)
    
        image = np.rollaxis(image, axis=2, start=0)[np.newaxis, :]
        return image
    
    def do_inference(self, artifact_path, image_name, model_name, model_shape):

        file_dir = artifact_path
        image_url = os.path.join(file_dir, image_name)
        output_url = os.path.join(file_dir, 'output.txt')
        labels_url = os.path.join(file_dir, 'image_net_labels.json')
        model_url = os.path.join(file_dir, model_name)
        
        with open(self.log_file, 'a') as f:
            print(model_shape, file=f)
            print(type(model_shape), file=f)
        
        SIZE = int(model_shape[1:-1].split(',')[2])
        
        with open(self.log_file, 'a') as f:
            print('SIZE: ' + str(SIZE), file=f)
        
        img = Image.open(image_url)
        with open(self.log_file, 'a') as f:
            print('img_load.shape: ' + str(np.shape(img)), file=f)
        img = np.asarray(img.resize((SIZE, SIZE)))
        img = self.transform(img)
        with open(self.log_file, 'a') as f:
            print('transform.shape: ' + str(np.shape(img)), file=f)
        
        model = dlr.DLRModel(model_url, 'cpu')
#         model = dlr.DLRModel(model_url, 'gpu', use_default_dlr=True) # for Jetson
        print("input_dtypes: {}".format(model.get_input_dtypes()))
        print("input_names: {}".format(model.get_input_names()))
        
        with open(self.log_file, 'a') as f:
            print(model.get_input_names(), file=f)
        
        print("model OK")
        
        input_name = model.get_input_names()[0]
        
        start = time.time() #　時間計測
        detections = model.run({input_name: img})[0]
        processing_time = time.time() - start
        print(processing_time)
            
        categories = np.array(json.load(open(labels_url, 'r')))
        
        index = np.argmax(detections[0])
        
        probability = detections[0][index]*100
        category = categories[index]
        result = "{}: {:.2f}%".format(category, probability)
        print(result)
        
        with open(self.log_file, 'a') as f:
            print('result: {}'.format(result), file=f)
            
        return [index, probability]
