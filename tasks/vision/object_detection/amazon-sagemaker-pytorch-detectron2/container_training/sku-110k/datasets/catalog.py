"""Add to Detectron2 catalog SKU-110k dataset"""
from typing import Sequence, Mapping, Tuple
from pathlib import Path
import json
from functools import partial
from dataclasses import dataclass
import sys
import logging

from detectron2.structures import BoxMode
from detectron2.data import MetadataCatalog, DatasetCatalog, Metadata

LOGGER = logging.Logger(name="Catalog", level=logging.INFO)
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
LOGGER.addHandler(HANDLER)


@dataclass
class DataSetMeta:
    r"""Dataset metadata

    Attributes
    ----------
        name : str
            dataset name
        classes : Sequence[str]
            class of objects to detect
    """

    name: str
    classes: Sequence[str]

    def __str__(self):
        """Print dataset name and class names"""
        return (
            f"The object detection dataset {self.name} "
            f"can detect {len(self.classes)} type(s) of objects: "
            f"{self.classes}"
        )


def remove_dataset(ds_name: str):
    r"""Remove a previously registered dataset

    Parameters
    ----------
    ds_name : str
        the dataset to be removed
    """
    for channel in ("training", "validation"):
        DatasetCatalog.remove(f"{ds_name}_{channel}")


def aws_file_mode(
    path_imgs: str, path_annotation: str, label_name: str
) -> Sequence[Mapping]:
    r"""Add dataset to Detectron by using the schema used by AWS for object detection

    Parameters
    ----------
    path_imgs : str
        path to folder that contains the images
    path_annotation : str
        path to the augmented manifest file that contains the annotations
    label_name : str
        label name used for object detection GT job

    Returns
    -------
    Sequence[Mapping]
        list of annotations

    Raises
    ------
    FileNotFoundError
        if the images to which the manifest file points to are not in path_imgs
    """
    dataset_dicts = []

    with open(path_annotation, "r") as ann_fid:
        for img_id, jsonline in enumerate(ann_fid):
            annotations = json.loads(jsonline)
            if "source-ref" not in annotations:
                err_msg = f"{path_annotation} is not a valid manifest file"
                LOGGER.error(err_msg)
                raise ValueError(err_msg)

            path_s3_img = Path(annotations["source-ref"])
            if path_s3_img.suffix.lower() not in (".png", ".jpg"):
                LOGGER.warning(
                    f"{path_s3_img.name} is not an image and it will be ignore"
                )
                continue
            local_path_to_img = Path(path_imgs) / path_s3_img.name
            if not local_path_to_img.exists():
                LOGGER.warning(
                    f"{path_s3_img.name} not found in image channel: annotations are neglected"
                )
                continue

            record = {
                "file_name": str(local_path_to_img),
                "height": annotations[label_name]["image_size"][0]["height"],
                "width": annotations[label_name]["image_size"][0]["width"],
                "image_id": img_id,
            }

            objs = []
            for bbox in annotations[label_name]["annotations"]:
                objs.append(
                    {
                        "bbox": [
                            bbox["left"],
                            bbox["top"],
                            bbox["width"],
                            bbox["height"],
                        ],
                        "bbox_mode": BoxMode.XYWH_ABS,
                        "category_id": bbox["class_id"],
                    }
                )
            record["annotations"] = objs
            dataset_dicts.append(record)

    return dataset_dicts


# pylint: disable=too-many-arguments
def register_dataset(
    metadata: DataSetMeta,
    label_name: str,
    channel_to_dataset: Mapping[str, Tuple[str, str]],
) -> Metadata:
    r"""Register training and validation datasets to detectron2

    Parameters
    ----------
    metadata : DataSetMeta
        metadata of the datasets to register
    label_name : str
        label name used for object detection GT job
    channel_to_dataset: Mapping[str, Tuple[str, str]]
        map channel name to dataset, each dataset is a 2D-tuple that contains path to images and
        path to augmented manifest file

    Returns
    -------
    Metadata
        Metadata file
    """

    for channel, datasets in channel_to_dataset.items():
        detectron_ds_name = f"{metadata.name}_{channel}"
        DatasetCatalog.register(
            detectron_ds_name,
            partial(aws_file_mode, datasets[0], datasets[1], label_name),
        )
        MetadataCatalog.get(detectron_ds_name).set(thing_classes=metadata.classes)
        LOGGER.info(f"{detectron_ds_name} dataset added to catalog")
    return MetadataCatalog.get(f"{metadata.name}_{list(channel_to_dataset.keys())[0]}")
