import json, pickle, tarfile, os, argparse
import numpy as np
import xgboost

from sklearn.metrics import roc_auc_score

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--thistime-train-model-dir', type=str, default=None)
    parser.add_argument('--lasttime-train-model-dir', type=str, default=None)
    parser.add_argument('--input-data-dir', type=str, default=None)
    parser.add_argument('--output-dir', type=str, default=None)
    parser.add_argument('--output-file', type=str, default='evaluation.json')
    
    args, _ = parser.parse_known_args()
    return args

def predict(input_model_dir:str, test_x):
    model_path = os.path.join(input_model_dir, 'model.tar.gz')
    with tarfile.open(model_path) as tar:
        
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, path=".")
    model = pickle.load(open("xgboost-model", "rb"))
    pred_y = model.predict(test_x)
    return pred_y

if __name__ == "__main__":
    args = arg_parse()
    
    test_csv_path = os.path.join(args.input_data_dir,'test.csv')
    test = np.loadtxt(test_csv_path, delimiter=',')
    test_x = xgboost.DMatrix(test[:,1:])
    answer_y = test[:,0]
    
    thistime_train_model_pred_y = predict(args.thistime_train_model_dir, test_x)
    lasttime_train_model_pred_y = predict(args.lasttime_train_model_dir, test_x)
    
    thistime_train_model_auc = roc_auc_score(answer_y,thistime_train_model_pred_y)
    lasttime_train_model_auc = roc_auc_score(answer_y,lasttime_train_model_pred_y)
    
    
    report_dict = {
        'classification_metrics': {
            'thistime_train_model_auc': {
                'value': thistime_train_model_auc,
            },
            'lasttime_train_model_auc': {
                'value': lasttime_train_model_auc,
            },
            'model_change':1 if thistime_train_model_auc > lasttime_train_model_auc else 0
        },
        'detail_result':{
            'thistime_train_model_pred_y': thistime_train_model_pred_y.tolist(),
            'lasttime_train_model_pred_y': lasttime_train_model_pred_y.tolist(),
            'answer_y': answer_y.tolist()
        }
    }
    print(report_dict)

    eval_result_path = os.path.join(args.output_dir, args.output_file)
    print(f'output save : {eval_result_path}')
    with open(eval_result_path, "w") as f:
        f.write(json.dumps(report_dict))
    print('post process done.')
    exit()
