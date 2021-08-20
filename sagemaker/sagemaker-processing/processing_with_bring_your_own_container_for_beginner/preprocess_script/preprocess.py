import argparse, os, zipfile
from glob import glob
from skimage import io
import numpy as np
import shutil

def hist_flatten(nparray):
    hist,bins = np.histogram(nparray.flatten(),256,[0,256])
    cdf = hist.cumsum()
    cdf_normalized = cdf * hist.max()/ cdf.max()
    cdf_m = np.ma.masked_equal(cdf,0)
    cdf_m = (cdf_m - cdf_m.min())*255/(cdf_m.max()-cdf_m.min())
    cdf = np.ma.filled(cdf_m,0).astype('uint8')
    return cdf[nparray]

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--hist-flatten', type=bool, default=False)
    parser.add_argument('--input-dir', type=str, default=None)
    parser.add_argument('--output-train-dir', type=str, default=None)
    parser.add_argument('--output-test-dir', type=str, default=None)
    
    args, _ = parser.parse_known_args()
    
    print('Received arguments {}'.format(args))

    input_data_path = os.path.join(args.input_dir, 'dataset.zip')
    
    print(f'decompress {input_data_path}')
    with zipfile.ZipFile(input_data_path) as existing_zip:
        existing_zip.extractall(args.input_dir)
    train_x = np.zeros((len(glob(args.input_dir + '/train_x/*.png')),28,28,1)).astype('float32')
    test_x = np.zeros((len(glob(args.input_dir + '/test_x/*.png')),28,28,1)).astype('float32')

    for i,img_file in enumerate(sorted(glob(args.input_dir + '/train_x/*.png'))):
        img = io.imread(img_file)
        if args.hist_flatten:
            img = hist_flatten(img)
        img = img/255.
        train_x[i,:,:,0] = img
    for i,img_file in enumerate(sorted(glob(args.input_dir + '/test_x/*.png'))):
        img = io.imread(img_file)
        if args.hist_flatten:
            img = hist_flatten(img)
        img = img/255.
        test_x[i,:,:,0] = img
    
    train_x_output_path = os.path.join(args.output_train_dir, 'train_x.npy')
    train_y_output_path = os.path.join(args.output_train_dir, 'train_y.npy')
    test_x_output_path = os.path.join(args.output_test_dir, 'test_x.npy')
    test_y_output_path = os.path.join(args.output_test_dir, 'test_y.npy')
    
    print(f'train_x save: {train_x_output_path}')
    np.save(train_x_output_path, train_x)
    print(f'train_y save: {train_y_output_path}')
    shutil.copyfile(args.input_dir + '/train_y.npy', train_y_output_path)
    
    print(f'test_x save: {test_x_output_path}')
    np.save(test_x_output_path, test_x)
    print(f'train_y save: {test_y_output_path}')
    shutil.copyfile(args.input_dir + '/test_y.npy', test_y_output_path)
