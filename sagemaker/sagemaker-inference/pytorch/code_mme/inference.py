"""Inference function overrides for SageMaker PyTorch serving container
"""
# Python Built-Ins:
import json
import logging
import sys
import os

# External Dependencies:
import torch

# Local Dependencies:
from model import Net

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

def model_fn(model_dir):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torch.nn.DataParallel(Net())
    with open(os.path.join(model_dir, 'model.pth'), 'rb') as f:
        model.load_state_dict(torch.load(f))
    return model.to(device)
