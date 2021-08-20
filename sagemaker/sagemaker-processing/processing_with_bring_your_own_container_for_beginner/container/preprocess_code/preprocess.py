import argparse, os, zipfile
from glob import glob
from PIL import Image
import pandas as pd
import numpy as np


def hist_flatten(nparray):
    hist,bins = np.histogram(nparray.flatten(),256,[0,256])
    cdf = hist.cumsum()
    cdf_normalized = cdf * hist.max()/ cdf.max()
    cdf_m = np.ma.masked_equal(cdf,0)
    cdf_m = (cdf_m - cdf_m.min())*255/(cdf_m.max()-cdf_m.min())
    cdf = np.ma.filled(cdf_m,0).astype('uint8')
    return cdf[nparray]

cdf = hist.cumsum()

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--hist-flatten', type=bool, default=False)
    args, _ = parser.parse_known_args()
    
    print('Received arguments {}'.format(args))

    input_data_path = os.path.join('/opt/ml/processing/input', 'img.zip')
    
    print(f'decompress {input_data_path}')
    with zipfile.ZipFile('data/temp/new_comp.zip') as existing_zip:
        existing_zip.extractall()
    train_x = np.zeros((len(glob('/opt/ml/processing/input/img/train_x/*.png')),28,28))
    test_x = np.zeros((len(glob('/opt/ml/processing/input/img/test_x/*.png')),28,28))

    for i,img_file in enumerate(sorted(glob('/opt/ml/processing/input/img/train_x/*.png'))):
        img = np.array(Image.open(img_file))
        if args.hist_flatten:
            img = hist_flatten(img)
        img = img/255.
        train_x[i,:,:] = img
    for i,img_file in enumerate(sorted(glob('/opt/ml/processing/input/img/test_x/*.png'))):
        img = np.array(Image.open(img_file))
        if args.hist_flatten:
            img = hist_flatten(img)
        img = img/255.
        test_x[i,:,:] = img
    
    train_features_output_path = '/opt/ml/processing/train/train_x.npy'
    test_features_output_path = '/opt/ml/processing/test/train_x.npy'
    
    print(f'train_x save: {train_features_output_path}')
    np.save('/opt/ml/processing/train/train_x.npy', train_x)
    print(f'test_x save: {test_features_output_path}')
    np.save('/opt/ml/processing/test/test_x.npy', test_x)
    