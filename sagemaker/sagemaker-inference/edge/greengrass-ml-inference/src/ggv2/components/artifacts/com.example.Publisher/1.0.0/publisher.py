from time import sleep
import datetime,json
import awsiot.greengrasscoreipc
from awsiot.greengrasscoreipc.model import (
    PublishToTopicRequest,
    PublishMessage,
    JsonMessage
)
from PIL import Image
import os, sys
import numpy as np
from logging import getLogger
logger = getLogger(__name__)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

logger.info(f'argv:{sys.argv}')

test_X_path = os.path.join(sys.argv[1],'test_X.npy')
test_X = np.load(test_X_path)

logger.info('start publisher...')

TIMEOUT = 10
interval = 60

ipc_client = awsiot.greengrasscoreipc.connect()

topic = "my/topic"

logger.info('start loop')

while True:
    # generate and save image file
    idx = np.random.randint(0,test_X.shape[0])
    file_name = '/tmp/' + datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y%m%d%H%M%S') + '.png'
    Image.fromarray(((test_X[idx,:,:,0]*127.5)+127.5).astype(np.uint8)).save(file_name)

    message = {"file_name": file_name }
    message_json = json.dumps(message).encode('utf-8')

    request = PublishToTopicRequest()
    request.topic = topic
    publish_message = PublishMessage()
    publish_message.json_message = JsonMessage()
    publish_message.json_message.message = message
    request.publish_message = publish_message
    operation = ipc_client.new_publish_to_topic()
    operation.activate(request)
    future = operation.get_response()
    future.result(TIMEOUT)

    logger.info(f'publish message: {message_json}')
    sleep(interval)
