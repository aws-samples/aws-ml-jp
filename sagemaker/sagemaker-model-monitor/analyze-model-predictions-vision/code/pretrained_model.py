from __future__ import print_function, division
import os

os.system('pip install Pillow')

import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
    
def model_fn(model_dir):
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

    return model

def transform_fn(model, data, content_type, output_content_type): 
    
    from torchvision import datasets, models, transforms
    import numpy as np
    from six import BytesIO
    from PIL import Image
    import json
    
    transform = transforms.Compose([ transforms.Resize((128,128)),
                                        transforms.ToTensor(),
                                        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                                        ])
    
    image = np.load(BytesIO(data))
    image = Image.fromarray(image)
    image = transform(image)
 
    image = image.unsqueeze(0)

    #forward pass
    prediction = model(image)

    #get prediction
    predicted_class = prediction.data.max(1, keepdim=True)[1]

    response_body = np.array(predicted_class.cpu()).tolist()
    return response_body, output_content_type
