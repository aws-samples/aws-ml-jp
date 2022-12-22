import io
import boto3
import time
import json
import math
import statistics
import uuid

import pandas as pd
import numpy as np
from sklearn import metrics
import sagemaker


def get_raw_data(year, month, sampling_rate=None):
    if isinstance(year, int):
        year = str(year)
    if isinstance(month, int):
        month = '{:02d}'.format(month)
    
    s3 = boto3.client('s3')

    nyc_bucket = 'nyc-tlc'
    key = 'trip data/yellow_tripdata_{}-{}.parquet'.format(year, month)

    s3_object = s3.get_object(Bucket=nyc_bucket, Key=key)
    byte_data = io.BytesIO(s3_object['Body'].read())
    df_read = pd.read_parquet(byte_data)
    
    if sampling_rate:
        df_read = df_read.sample(n=int(df_read.shape[0]/100*sampling_rate))
        
    df_read = df_read[
        (df_read.tpep_pickup_datetime.dt.year==int(year)) & 
        (df_read.tpep_pickup_datetime.dt.month==int(month))].copy()
    
    return df_read


def hours_to_15mins_slot(from_hour, to_hour, step=1):
    return [x for x in range(from_hour*4, to_hour*4, step)]


def extract_features(df_raw):
    # Define group by key cols
    df_raw['date'] = df_raw.tpep_pickup_datetime.dt.date
    df_raw['time_slot'] = df_raw.tpep_pickup_datetime.apply(lambda x: int((x.hour*60+x.minute)/15))

    # Drop abnormal records based on trip duration (sec)
    df_raw['trip_delta'] = df_raw.tpep_dropoff_datetime - df_raw.tpep_pickup_datetime
    df_raw['trip_duration_sec'] = df_raw.trip_delta.dt.total_seconds()
    df_raw = df_raw[(10 < df_raw.trip_duration_sec) & (df_raw.trip_duration_sec <= 14400)]

    g = df_raw.groupby(by=['date', 'time_slot'])
    df_summary = pd.DataFrame()
    df_summary['pickup_count'] = g['date'].count()

    lookback_slots = []
    lookback_slots.extend(hours_to_15mins_slot(3, 72,4))
    lookback_slots.extend(hours_to_15mins_slot(24*7-2, 24*7+1, 2))
    lookback_slots.extend(hours_to_15mins_slot(24*14-2, 24*14+1, 2))
    lookback_slots.extend(hours_to_15mins_slot(24*21-2, 24*21+1, 2))
    for i, slot in enumerate(lookback_slots):
        df_summary[f'history_{slot}slots'] = df_summary.pickup_count.shift(slot)
        # Copy to refresh DataFrame
        if i % 10 == 0:
            df_summary = df_summary.copy()

    df_summary = df_summary.copy()
    df_summary

    lookback_slots = []
    lookback_slots.extend(hours_to_15mins_slot(3, 6, 4))
    lookback_slots.extend(hours_to_15mins_slot(24, 27, 4))
    lookback_slots.extend(hours_to_15mins_slot(48, 51, 4))
    for feature in ['passenger_count', 'trip_distance', 'fare_amount', 'extra', 'tip_amount', 'tolls_amount']:
        df_summary[f'{feature}_mean'] = g[feature].mean()
        for i,slot in enumerate(lookback_slots):
            df_summary[f'{feature}_mean_{slot}slot'] = df_summary[f'{feature}_mean'].shift(slot)
            # Copy to refresh DataFrame
            if i % 10 == 0:
                df_summary = df_summary.copy()
                
        df_summary = df_summary.drop(columns=[f'{feature}_mean'])
    
    # Move time_slot from index to column
    df_summary = df_summary.reset_index().set_index('date')
    
    # Move time_slot to tail
    columns = df_summary.columns.to_list()
    columns.remove('time_slot')
    columns.append('time_slot')
    df_summary = df_summary[columns]
        
    return df_summary


def filter_current_month(df, year, month):
    if isinstance(year, int):
        year = str(year)
    if isinstance(month, int):
        month = '{:02d}'.format(month)

    start_date = pd.to_datetime('{}-{}-01'.format(year, month))
    end_date = start_date + pd.offsets.MonthEnd()
    df_range = pd.DataFrame(index=pd.date_range(start_date, end_date, freq='D'))

    df_filterd = pd.merge(df_range, df, how='left', left_index=True, right_index=True)
    
    return df_filterd


def get_previous_year_month(year, month):
    current_date = pd.to_datetime(f'{year}-{month}-01')
    previous_date = current_date - pd.offsets.Day(1)
    return previous_date.year, previous_date.month


def calc_accuracy(y, pred):
    print('RMSE:', np.sqrt(metrics.mean_squared_error(y, pred)))
    print('MAE:', metrics.mean_absolute_error(y, pred))
    print('R2:', metrics.r2_score(y, pred))
    

def call_model_endpoint(endpoint_name, payload, inference_id):
    runtime_client = boto3.client('runtime.sagemaker')
    response = runtime_client.invoke_endpoint(
        EndpointName=endpoint_name,                                               
        ContentType='text/csv',
        InferenceId=inference_id,
        Body=payload)

    result = response['Body'].read().decode("utf-8")
    result = result.split(',')
    result = [math.ceil(float(i)) for i in result]
    return result[0]


def exec_prediction(endpoint_name, df):
    df_csv = df.copy()
    df_csv = df.drop(columns=[df.columns[0]])
    csv = df_csv.to_csv(header=False, index=False)
    
    all_pred = []
    for payload in csv.split('\n')[:-1]:
        inference_id = str(uuid.uuid4())
        prediction = call_model_endpoint(endpoint_name, payload, inference_id)
        all_pred.append([prediction, inference_id])

    return all_pred