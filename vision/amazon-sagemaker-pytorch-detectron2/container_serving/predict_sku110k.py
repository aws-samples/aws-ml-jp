"""Code used for sagemaker batch transform jobs"""
from typing import BinaryIO, Mapping
import json
import logging
import sys
from pathlib import Path

import numpy as np
import cv2
import torch

from detectron2.engine import DefaultPredictor
from detectron2.config import CfgNode

##############
# Macros
##############

LOGGER = logging.Logger("InferenceScript", level=logging.INFO)
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
LOGGER.addHandler(HANDLER)

##########
# Deploy
##########
def _load_from_bytearray(request_body: BinaryIO) -> np.ndarray:
    npimg = np.frombuffer(request_body, np.uint8)
    return cv2.imdecode(npimg, cv2.IMREAD_COLOR)


def model_fn(model_dir: str) -> DefaultPredictor:
    r"""Load trained model

    Parameters
    ----------
    model_dir : str
        S3 location of the model directory

    Returns
    -------
    DefaultPredictor
        PyTorch model created by using Detectron2 API
    """
    path_cfg, path_model = None, None
    for p_file in Path(model_dir).iterdir():
        if p_file.suffix == ".json":
            path_cfg = p_file
        if p_file.suffix == ".pth":
            path_model = p_file

    LOGGER.info(f"Using configuration specified in {path_cfg}")
    LOGGER.info(f"Using model saved at {path_model}")

    if path_model is None:
        err_msg = "Missing model PTH file"
        LOGGER.error(err_msg)
        raise RuntimeError(err_msg)
    if path_cfg is None:
        err_msg = "Missing configuration JSON file"
        LOGGER.error(err_msg)
        raise RuntimeError(err_msg)

    with open(str(path_cfg)) as fid:
        cfg = CfgNode(json.load(fid))

    cfg.MODEL.WEIGHTS = str(path_model)
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    return DefaultPredictor(cfg)


def input_fn(request_body: BinaryIO, request_content_type: str) -> np.ndarray:
    r"""Parse input data

    Parameters
    ----------
    request_body : BinaryIO
        encoded input image
    request_content_type : str
        type of content

    Returns
    -------
    np.ndarray
        input image

    Raises
    ------
    ValueError
        ValueError if the content type is not `application/x-image`
    """
    if request_content_type == "application/x-image":
        np_image = _load_from_bytearray(request_body)
    else:
        err_msg = f"Type [{request_content_type}] not support this type yet"
        LOGGER.error(err_msg)
        raise ValueError(err_msg)
    return np_image


def predict_fn(input_object: np.ndarray, predictor: DefaultPredictor) -> Mapping:
    r"""Run Detectron2 prediction

    Parameters
    ----------
    input_object : np.ndarray
        input image
    predictor : DefaultPredictor
        Detectron2 default predictor (see Detectron2 documentation for details)

    Returns
    -------
    Mapping
        a dictionary that contains: the image shape (`image_height`, `image_width`), the predicted
        bounding boxes in format x1y1x2y2 (`pred_boxes`), the confidence scores (`scores`) and the
        labels associated with the bounding boxes (`pred_boxes`)
    """
    LOGGER.info(f"Prediction on image of shape {input_object.shape}")
    outputs = predictor(input_object)
    fmt_out = {
        "image_height": input_object.shape[0],
        "image_width": input_object.shape[1],
        "pred_boxes": outputs["instances"].pred_boxes.tensor.tolist(),
        "scores": outputs["instances"].scores.tolist(),
        "pred_classes": outputs["instances"].pred_classes.tolist(),
    }
    LOGGER.info(f"Number of detected boxes: {len(fmt_out['pred_boxes'])}")
    return fmt_out


# pylint: disable=unused-argument
def output_fn(predictions, response_content_type):
    r"""Serialize the prediction result into the desired response content type"""
    return json.dumps(predictions)
