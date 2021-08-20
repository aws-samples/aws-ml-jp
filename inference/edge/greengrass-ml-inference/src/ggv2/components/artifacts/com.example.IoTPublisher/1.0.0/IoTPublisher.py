from time import sleep
import datetime,json
from awsiot.greengrasscoreipc import connect
from awsiot.greengrasscoreipc.model import (
    QOS,
    PublishToIoTCoreRequest
)
import tensorflow as tf
from PIL import Image
import os, sys
import numpy as np
import signal
from logging import getLogger
logger = getLogger(__name__)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

TIMEOUT = 10
INTERVAL = 60

ipc_client = connect()

test_X = np.load('/app/test_X.npy')

classifier_model = tf.keras.models.load_model('/app/classifier.h5')

topic = "inference/result"

def signal_handler(signal, frame):
    logger.info(f"Received {signal}, exiting")
    sys.exit(0)

# Register SIGTERM for shutdown of container
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

cnt = 0
while True:
    
    idx = np.random.randint(0,test_X.shape[0])
    img_array = test_X[idx:idx+1,:,:,:]
    
    pred_y = np.argmax(classifier_model.predict(img_array))
    
    result = 'anomaly' if pred_y % 2 == 0 else 'normal'

    cnt = cnt + 1
    message = {
        "timestamp": str(datetime.datetime.now()), 
        "message": result,
        "counter": str(cnt),
        "component_version" : "1.0.0"
    }

    request = PublishToIoTCoreRequest(topic_name=topic, qos=QOS.AT_LEAST_ONCE, payload=bytes(json.dumps(message), "utf-8"))
    operation = ipc_client.new_publish_to_iot_core()
    operation.activate(request)
    future = operation.get_response()
    future.result(TIMEOUT)
    
    logger.info("publish")
    sleep(INTERVAL)
