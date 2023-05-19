import time, json, sys, os
import awsiot.greengrasscoreipc
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc.model import (
    SubscribeToTopicRequest,
    SubscriptionResponseMessage
)
import tensorflow as tf
import numpy as np
from PIL import Image
from logging import getLogger
logger = getLogger(__name__)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

logger.info(f'argv:{sys.argv}')

model_path = os.path.join(sys.argv[1],'classifier.h5')

logger.info('start subscriber...')

TIMEOUT = 10

logger.info('start to load model')
model = tf.keras.models.load_model(model_path)

ipc_client = awsiot.greengrasscoreipc.connect()

class StreamHandler(client.SubscribeToTopicStreamHandler):
    def __init__(self):
        super().__init__()

    def on_stream_event(self, event: SubscriptionResponseMessage) -> None:
        message_string = event.json_message.message
        file_path = message_string['file_name']
        logger.info(f'recieved message: {file_path}')
        img = Image.open(file_path)
        img = (np.array(img).reshape(1,28,28,1)-127.5)/127.5
        pred_y = np.argmax(model.predict(img))
        with open('/tmp/Greengrass_Subscriber.log', 'a') as f:
            f.write(f'{file_path}\n')
            f.write(f'{img.shape}\n')
            f.write(f'{pred_y}\n')
            f.write('even\n') if pred_y % 2 == 0 else f.write('odd\n')
        # 処理済ファイルを削除
        os.remove(file_path)

    def on_stream_error(self, error: Exception) -> bool:
        return True

    def on_stream_closed(self) -> None:
        pass

topic = "my/topic"

request = SubscribeToTopicRequest()
request.topic = topic
handler = StreamHandler()
operation = ipc_client.new_subscribe_to_topic(handler)
future = operation.activate(request)
while True:
    time.sleep(1)

operation.close()
