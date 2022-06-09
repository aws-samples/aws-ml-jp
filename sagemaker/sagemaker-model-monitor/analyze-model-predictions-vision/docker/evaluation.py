import argparse
import datetime
import numpy as np
import json
import os
import glob
import sys

if __name__=="__main__":
    
    files = glob.glob("/opt/ml/processing/input/endpoint/*/*/*/*/*/*/*")
    predictions = []
    for file in files:
        content = open(file).read() 
        for entry in content.split('\n'):
            try:
                prediction = json.loads(entry)['captureData']['endpointOutput']['data']
                predictions.append(json.loads(prediction)[0][0])
            except:
                pass
    counts = {}
    max_count = 0
    max_class = 0
    for prediction in predictions:
        if prediction not in counts:
            counts[prediction] = 0
        counts[prediction] += 1
        if counts[prediction] > max_count:
            max_count = counts[prediction] 
            max_class = prediction

    ratio = max_count/np.sum(list(counts.values()))
    
    with open('/opt/ml/output/message', 'w') as outfile:
        if(ratio > float(os.environ['THRESHOLD'])):
            outfile.write(f"CompletedWithViolations: Class {max_class} predicted more than {int(ratio*100)} % of the time")
            print(f"Class {max_class} predicted more than {int(ratio*100)} % of the time")
        else:
            outfile.write("Completed: Job completed successfully with no violations.")
    outfile.close()
    
    print(f"Predicted classes {str(counts)}")
    
    outfile = open('/opt/ml/output/metrics/cloudwatch/cloudwatch_metrics.jsonl', 'a+') 
    for key, val in counts.items():
        output_dict = { 
            "MetricName": "Predicted Class " + str(key), 
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), 
            "Dimensions" : [{"Name":"Endpoint","Value":"endpoint_0"},{"Name":"MonitoringSchedule","Value":"schedule_0"}],
            "Value": val
        }
        #one metric per line (list of dictionaries)
        json.dump(output_dict, outfile)
        outfile.write("\n")
    outfile.close()
