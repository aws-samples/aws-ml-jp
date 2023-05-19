# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import time
import datetime
import json
import sys
import glob
import awsiot.greengrasscoreipc
from awsiot.greengrasscoreipc.model import (
    QOS,
    PublishToIoTCoreRequest,
    PublishToTopicRequest,
    PublishMessage,
    JsonMessage
)
from inference import Inference

publish_rate = 0.2

ipc_client = awsiot.greengrasscoreipc.connect()
inf = Inference()
                    
while True:
    with open('/tmp/Greengrass_HelloWorld.log', 'a') as f:
        print(sys.argv[1], file=f)
    result = inf.do_inference(sys.argv[1], "classification-demo.png", 'model', sys.argv[2])

    time.sleep(1/publish_rate)
