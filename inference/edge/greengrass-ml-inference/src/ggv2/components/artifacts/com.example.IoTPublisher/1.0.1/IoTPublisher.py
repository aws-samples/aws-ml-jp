from time import sleep
import dlr, datetime, json, os, sys, signal
from awsiot.greengrasscoreipc import connect
from awsiot.greengrasscoreipc.model import (
    QOS,
    PublishToIoTCoreRequest
)
import numpy as np
from logging import getLogger
logger = getLogger(__name__)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# メッセージに thing_name を入れるために thing_name を環境変数から取得する
THING_NAME = os.environ.get('AWS_IOT_THING_NAME')

TIMEOUT = 10

ipc_client = connect()

INTERVAL = 60

neo_dir = '/app/classifier'
classifier_neo = dlr.DLRModel(neo_dir, 'cpu', 0)

test_X = np.load('/app/test_X.npy')

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
    
    pred_y = np.argmax(classifier_neo.run(test_X[0,:,:,:].reshape(1,1,28,28))[0])
    
    result = 'anomaly' if pred_y % 2 == 0 else 'normal'

    cnt = cnt + 1
    message = {
        "timestamp": str(datetime.datetime.now()), 
        "message": result,
        "counter": str(cnt),
        "component_version" : "1.0.1",
        "thing_name" : THING_NAME
    }

    request = PublishToIoTCoreRequest(topic_name=topic, qos=QOS.AT_LEAST_ONCE, payload=bytes(json.dumps(message), "utf-8"))
    operation = ipc_client.new_publish_to_iot_core()
    operation.activate(request)
    future = operation.get_response()
    future.result(TIMEOUT)
    
    logger.info("publish")
    sleep(INTERVAL)
