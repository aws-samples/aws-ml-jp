"""Inference function overrides for SageMaker PyTorch serving container
"""
# Python Built-Ins:
import numpy as np
import io
import torch
import json

def input_fn(request_body, request_content_type):
    data = np.load(io.BytesIO(request_body))
    data = torch.from_numpy(data).clone()
    return data
