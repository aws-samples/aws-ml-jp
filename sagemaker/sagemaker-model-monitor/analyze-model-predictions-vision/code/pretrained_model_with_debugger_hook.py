from __future__ import print_function, division
import os

os.system('pip install Pillow sagemaker smdebug==0.5.0')

import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models

import smdebug.pytorch as smd
from smdebug import modes
from smdebug.core.modes import ModeKeys
from custom_hook import CustomHook
import sagemaker
import boto3

hook = None
def model_fn(model_dir):
    global hook
    #create model    
    model = models.resnet18()

    #traffic sign dataset has 43 classes   
    nfeatures = model.fc.in_features
    model.fc = nn.Linear(nfeatures, 43)
    
    #load model
    weights = torch.load(model_dir + '/model/model.pt', map_location=lambda storage, loc: storage)
    model.load_state_dict(weights)
    
    model.eval()
    model.cpu()

    #hook configuration
    save_config = smd.SaveConfig(mode_save_configs={
        smd.modes.PREDICT: smd.SaveConfigMode(save_interval=1)
    })
    
    boto_session = boto3.Session()
    sagemaker_session = sagemaker.Session(boto_session=boto_session)    

    hook = CustomHook("s3://" + sagemaker_session.default_bucket() + "/endpoint/tensors", 
                    save_config=save_config, 
                    include_regex='.*bn|.*bias|.*downsample|.*ResNet_input|.*image|.*fc_output' )
    
    #register hook
    hook.register_module(model) 
    
    #set mode
    hook.set_mode(modes.PREDICT)

    return model

def transform_fn(model, data, content_type, output_content_type): 
    
    from torchvision import datasets, models, transforms
    import numpy as np
    from six import BytesIO
    from PIL import Image
    import json
    
    val_transform = transforms.Compose([ transforms.Resize((128,128)),
                                        transforms.ToTensor(),
                                        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                                        ])
    
    image = np.load(BytesIO(data))
    image = Image.fromarray(image)
    image = val_transform(image)
 
    image = image.unsqueeze(0)
    image = image.to('cpu').requires_grad_()
    hook.image_gradients(image)

    #forward pass
    prediction = model(image)

    #get prediction
    predicted_class = prediction.data.max(1, keepdim=True)[1]
    output = prediction[0,predicted_class[0]]
    model.zero_grad()
    
    #compute gradients with respect to outputs 
    output.backward()

    response_body = np.array(predicted_class.cpu()).tolist()
    return response_body, output_content_type

