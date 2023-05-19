# churn データの前処理スクリプト
# 前処理内容は下記と同じ
# https://github.com/aws-samples/amazon-sagemaker-examples-jp/blob/master/xgboost_customer_churn/xgboost_customer_churn.ipynb
# State, Area Code, VMail Plan などをダミー変数化するところは、全ての週が分けたデータに入っているか不透明だったため、ハードコーディングでダミー変数化する

import pandas as pd
import numpy as np
import argparse
from sklearn.model_selection import train_test_split
import os
from glob import glob

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-data-input-dir', type=str, default=None)
    parser.add_argument('--pre-processed-train-data-input-dir', type=str, default=None)
    parser.add_argument('--pre-processed-valid-data-input-dir', type=str, default=None)
    parser.add_argument('--pre-processed-test-data-input-dir', type=str, default=None)
    parser.add_argument('--train-output-dir', type=str, default=None)
    parser.add_argument('--valid-output-dir', type=str, default=None)
    parser.add_argument('--test-output-dir', type=str, default=None)
    parser.add_argument('--merge' , action='store_true')
    args, _ = parser.parse_known_args()
    return args

if __name__=='__main__':
    args = arg_parse()
    # csv ファイルの読み込み
    # 複数ファイルが raw_input_dir に配置されたら全て縦に concat する
    df_list = []
    for csv_file in glob(args.raw_data_input_dir+'/*.csv'):
        tmp_df = pd.read_csv(csv_file)
        df_list.append(tmp_df)
    df = pd.concat(df_list,axis=0)
    
    # 不要カラムの除去
    df = df.drop(['Phone','Day Charge', 'Eve Charge', 'Night Charge', 'Intl Charge'], axis=1)
    
    # Area Code のダミー変数化
    df['Area Code'] = df['Area Code'].astype(object)
    area_code_list = ['415', '408', '510']
    for area_code in area_code_list:
        df[area_code] = df['Area Code'].map(lambda x: 1 if x==area_code else 0)
    df = df.drop(['Area Code'],axis=1)
    
    # State のダミー変数化
    states_list = ['KS', 'OH', 'NJ', 'OK', 'AL', 'MA', 'MO', 'LA', 'WV', 'IN', 'RI', 'IA', 'MT', 'NY', 'ID', 'VT', 'VA', 'TX', 'FL', 'CO', 'AZ', 'SC', 'NE', 'WY', 'HI', 'IL', 'NH', 'GA', 'AK', 'MD', 'AR', 'WI', 'OR', 'MI', 'DE', 'UT', 'CA', 'MN', 'SD', 'NC', 'WA', 'NM', 'NV', 'DC', 'KY', 'ME', 'MS', 'TN', 'PA', 'CT', 'ND']
    for state in states_list:
        df[state] = df['State'].map(lambda x: 1 if x==state else 0)
    df = df.drop(['State'],axis=1)
    
    # Int'l Plan のダミー変数化
    intl_plan_list = ['yes','no']
    for intl_plan in intl_plan_list:
        df[f'intl_plan{intl_plan}'] = df["Int'l Plan"].map(lambda x: 1 if x==intl_plan else 0)
    df = df.drop(["Int'l Plan"],axis=1)
    
    # Vmail Plan のダミー変数化
    vmail_plan_list = ['yes','no']
    for vmail_plan in vmail_plan_list:
        df[f'vmail_plan{vmail_plan}'] = df["VMail Plan"].map(lambda x: 1 if x==vmail_plan else 0)
    df = df.drop(["VMail Plan"],axis=1)
    
    # churn? の 1/0 化 (xgboost のデータ入力仕様)
    df['y'] = df['Churn?'].map(lambda x: 1 if x=='True.' else 0)
    df = df.drop(['Churn?'], axis=1)
    
    # 予測したいカラムを最初に持ってくる (xgboost のデータ入力仕様)
    df = pd.concat([df.iloc[:,-1],df.iloc[:,:-1]],axis=1)
    train_df, valid_df, test_df = np.split(df.sample(frac=1, random_state=42), [int(0.7 * len(df)), int(0.9 * len(df))])
    
    # 過去の前処理済データをマージ
    if args.merge:
        # train
        lasttime_train_input_path = os.path.join(args.pre_processed_train_data_input_dir, 'train.csv')
        lasttime_train_df = pd.read_csv(lasttime_train_input_path, header=None, names=df.columns.tolist())
        train_df = pd.concat([train_df,lasttime_train_df],axis=0)
        # valid
        lasttime_valid_input_path = os.path.join(args.pre_processed_valid_data_input_dir, 'valid.csv')
        lasttime_valid_df = pd.read_csv(lasttime_valid_input_path, header=None, names=df.columns.tolist())
        valid_df = pd.concat([valid_df,lasttime_valid_df],axis=0)
        # test
        lasttime_test_input_path = os.path.join(args.pre_processed_test_data_input_dir, 'test.csv')
        lasttime_test_df = pd.read_csv(lasttime_test_input_path, header=None, names=df.columns.tolist())
        test_df = pd.concat([test_df,lasttime_test_df],axis=0)
    
    train_output_path = os.path.join(args.train_output_dir, 'train.csv')
    valid_output_path = os.path.join(args.valid_output_dir, 'valid.csv')
    test_output_path = os.path.join(args.test_output_dir, 'test.csv')
    
    train_df.to_csv(train_output_path, header=False, index=False)
    valid_df.to_csv(valid_output_path, header=False, index=False)
    test_df.to_csv(test_output_path, header=False, index=False)
    
    exit()