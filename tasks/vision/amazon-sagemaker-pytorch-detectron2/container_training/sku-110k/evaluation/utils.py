"""General Utils"""
from pathlib import Path
import json
from typing import Mapping, Tuple

import torch
from detectron2.evaluation.coco_evaluation import instances_to_coco_json
from detectron2.structures import Instances, Boxes


def _annotation_from_single_img(
    p_data: Mapping, p_img_id: int, label_name: str
) -> Tuple[Mapping, Mapping, int]:
    """
    Convert annotations on a single image from detectron2 format to COCO one

    Args:
        p_data ([type]): raw annotation
        p_img_id ([type]): current image id
        label_name (str): label name in raw annotations

    Returns:
        Tuple[Mapping, Mapping, int]: COCO image metadata, COCO annotation, next image id
    """
    out_images = {
        "id": p_img_id,
        "width": p_data[label_name]["image_size"][0]["width"],
        "height": p_data[label_name]["image_size"][0]["height"],
        "file_name": p_data["source-ref"],
    }
    out_annotations = []
    ann_id = p_img_id
    for elem in p_data["sku"]["annotations"]:
        out_annotations.append(
            {
                "id": ann_id,
                "image_id": p_img_id,
                "category_id": elem["class_id"],
                "bbox": [elem["left"], elem["top"], elem["width"], elem["height"]],
                "iscrowd": 0,
                "area": float(elem["width"] * elem["height"]),
            }
        )
        ann_id += 1

    return out_images, out_annotations, ann_id


def annotation_to_coco(s3_obj_iter):
    """Convert all the annotations to COCO style"""
    out_images = []
    out_annotations = []
    img_id = 0
    for ann_obj in s3_obj_iter:
        if Path(ann_obj.key).suffix != ".json":
            continue

        data = json.loads(ann_obj.get()["Body"].read().decode("utf-8"))

        elem_img, elem_ann, img_id = _annotation_from_single_img(data, img_id)
        out_images.append(elem_img)
        out_annotations += elem_ann
    return out_images, out_annotations


def convert_to_d2_preds(json_data) -> Instances:
    """convert detectron2 raw predictions to Detectron2 format"""
    f_out = Instances((json_data["image_height"], json_data["image_width"]))
    f_out.pred_boxes = Boxes(torch.tensor(json_data["pred_boxes"]))
    f_out.scores = torch.tensor(json_data["scores"])
    f_out.pred_classes = torch.tensor(json_data["pred_classes"])
    return f_out
