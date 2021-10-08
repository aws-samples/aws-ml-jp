"""Inference function overrides for SageMaker PyTorch serving container
"""
# Python Built-Ins:
import json
import logging
import sys
import os
import io

# External Dependencies:
import torch

# Local Dependencies:
from model import Net

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def model_fn(model_dir):
    model = torch.nn.DataParallel(Net())
    with open(os.path.join(model_dir, 'model.pth'), 'rb') as f:
        model.load_state_dict(torch.load(f))
    return model.to(device)

def input_fn(request_body, request_content_type):
    """Validate, de-serialize and pre-process requests"""
    data = torch.load(io.BytesIO(request_body))
    data = torch.tensor(data, dtype=torch.float32, device=device)
    return data

def predict_fn(input_object, model):
    """Execute the model on input data"""
    with torch.no_grad():
        model.eval()
        prediction = model(input_object)
    return prediction

def output_fn(predictions, content_type):
    """Post-process and serialize model output to API response"""
    print('result:', predictions)
    res = predictions.cpu().numpy().tolist()
    return json.dumps(res)
