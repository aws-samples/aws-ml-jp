"""Create annotation files"""
from typing import Sequence
import json

from pycocotools.coco import COCO

from evaluation.utils import annotation_to_coco


def generate_ground_truth(
    dataset_description: str, categories: Sequence[str], s3_objs, fname: str
):
    """TODO add doc"""
    info = {
        "year": 2020,
        "version": "0.0",
        "description": "SKU-110k",
    }
    cat = [
        {"id": cat_id, "name": cat_name} for cat_id, cat_name in enumerate(categories)
    ]

    images, annotations = annotation_to_coco(s3_objs)

    coco_annotation = {
        "info": info,
        "images": images,
        "annotations": annotations,
        "categories": cat,
    }

    with open(fname, "w") as fid:
        json.dump(coco_annotation, fid)

    return COCO(fname), coco_annotation


def generate_predictions(s3_pred_objects: Sequence, image_ids: Sequence[int], coco_gt, fname: str):
    
    assert len(s3_pred_objects) == len(image_ids), f"Mismatch nb of objects ({len(s3_pred_objects)}) vs nb of identifiers ({len(image_ids)})"

    predictions = []
    for pred_obj, elem in zip(s3_pred_objects, image_ids):
        preds = json.loads(pred_obj.get()["Body"].read().decode("utf-8"))
        predictions += instances_to_coco_json(convert_to_d2_preds(preds), elem["id"])

    with open(fname, 'w') as fid:
        json.dump(predictions, fid)
        
    return coco_gt.loadRes(fname)