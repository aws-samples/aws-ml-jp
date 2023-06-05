"""Entry point of the Detectron2 container that is used to train models on SKU-110k dataset"""
import os
import argparse
import logging
import sys
import ast
import json
from pathlib import Path

from detectron2.engine import launch
from detectron2.config import get_cfg, CfgNode
from detectron2 import model_zoo
from detectron2.checkpoint import DetectionCheckpointer

from datasets.catalog import register_dataset, DataSetMeta
from engine.custom_trainer import Trainer
from evaluation.coco import D2CocoEvaluator

##############
# Macros
##############
LOGGER = logging.Logger("TrainingScript", level=logging.INFO)
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
LOGGER.addHandler(HANDLER)

########################
# Implementation Details
########################


def _config_training(args: argparse.Namespace) -> CfgNode:
    r"""Create a configuration node from the script arguments.

    In this application we consider object detection use case only. We finetune object detection
    networks trained on COCO dataset to a custom use case

    Parameters
    ----------
    args : argparse.Namespace
        training script arguments, see :py:meth:`_parse_args()`

    Returns
    -------
    CfgNode
        configuration that is used by Detectron2 to train a model

    Raises:
        RuntimeError: if the combination of `model_type`, `backbone`, `lr_schedule` is not valid.
            Please refer to Detectron2 model zoo for valid options.
    """
    cfg = get_cfg()
    pretrained_model = (
        f"COCO-Detection/{args.model_type}_{args.backbone}_{args.lr_schedule}x.yaml"
    )
    LOGGER.info(f"Loooking for the pretrained model {pretrained_model}...")
    try:
        cfg.merge_from_file(model_zoo.get_config_file(pretrained_model))
    except RuntimeError as err:
        LOGGER.error(f"{err}: check model backbone and lr schedule combination")
        raise
    cfg.DATASETS.TRAIN = (f"{args.dataset_name}_training",)
    cfg.DATASETS.TEST = (f"{args.dataset_name}_validation",)
    cfg.DATALOADER.NUM_WORKERS = args.num_workers
    # Let training initialize from model zoo
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(pretrained_model)
    LOGGER.info(f"{pretrained_model} correctly loaded")

    cfg.SOLVER.CHECKPOINT_PERIOD = 20000
    cfg.SOLVER.BASE_LR = args.lr
    cfg.SOLVER.MAX_ITER = args.num_iter
    cfg.SOLVER.IMS_PER_BATCH = args.batch_size
    cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = args.num_rpn
    if args.model_type == "faster_rcnn":
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = len(args.classes)
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = args.pred_thr
        cfg.MODEL.ROI_HEADS.NMS_THRESH_TEST = args.nms_thr
        cfg.MODEL.RPN.BBOX_REG_LOSS_TYPE = args.reg_loss_type
        cfg.MODEL.RPN.BBOX_REG_LOSS_WEIGHT = args.bbox_reg_loss_weight
        cfg.MODEL.RPN.POSITIVE_FRACTION = args.bbox_rpn_pos_fraction
        cfg.MODEL.ROI_HEADS.POSITIVE_FRACTION = args.bbox_head_pos_fraction
    elif args.model_type == "retinanet":
        cfg.MODEL.RETINANET.SCORE_THRESH_TEST = args.pred_thr
        cfg.MODEL.RETINANET.NMS_THRESH_TEST = args.nms_thr
        cfg.MODEL.RETINANET.NUM_CLASSES = len(args.classes)
        cfg.MODEL.RETINANET.BBOX_REG_LOSS_TYPE = args.reg_loss_type
        cfg.MODEL.RETINANET.FOCAL_LOSS_GAMMA = args.focal_loss_gamma
        cfg.MODEL.RETINANET.FOCAL_LOSS_ALPHA = args.focal_loss_alpha
    else:
        assert False, f"Add implementation for model {args.model_type}"
    cfg.MODEL.DEVICE = "cuda" if args.num_gpus else "cpu"

    cfg.TEST.DETECTIONS_PER_IMAGE = args.det_per_img

    cfg.OUTPUT_DIR = args.model_dir
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    return cfg


def _train_impl(args) -> None:
    r"""Training implementation executes the following steps:

        * Register the dataset to Detectron2 catalog
        * Create the configuration node for training
        * Launch training
        * Serialize the training configuration to a JSON file as it is required for prediction
    """

    dataset = DataSetMeta(name=args.dataset_name, classes=args.classes)

    for ds_type in (
        ("training", "validation", "test")
        if args.evaluation_type
        else ("training", "validation",)
    ):
        if not Path(args.annotation_channel) / f"{ds_type}.manifest":
            err_msg = f"{ds_type} dataset annotations not found"
            LOGGER.error(err_msg)
            raise FileNotFoundError(err_msg)

    channel_to_ds = {
        "training": (
            args.training_channel,
            f"{args.annotation_channel}/training.manifest",
        ),
        "validation": (
            args.validation_channel,
            f"{args.annotation_channel}/validation.manifest",
        ),
    }
    if args.evaluation_type:
        channel_to_ds["test"] = (
            args.test_channel,
            f"{args.annotation_channel}/test.manifest",
        )

    register_dataset(
        metadata=dataset, label_name=args.label_name, channel_to_dataset=channel_to_ds,
    )

    cfg = _config_training(args)

    cfg.setdefault("VAL_LOG_PERIOD", args.log_period)

    trainer = Trainer(cfg)
    trainer.resume_or_load(resume=False)

    if cfg.MODEL.DEVICE != "cuda":
        err = RuntimeError("A CUDA device is required to launch training")
        LOGGER.error(err)
        raise err
    trainer.train()

    # If in the master process: save config and run COCO evaluation on test set
    if args.current_host == args.hosts[0]:
        with open(f"{cfg.OUTPUT_DIR}/config.json", "w") as fid:
            json.dump(cfg, fid, indent=2)

        if args.evaluation_type:
            LOGGER.info(f"Running {args.evaluation_type} evaluation on the test set")
            evaluator = D2CocoEvaluator(
                dataset_name=f"{dataset.name}_test",
                tasks=("bbox",),
                distributed=len(args.hosts)==1 and args.num_gpus > 1,
                output_dir=f"{cfg.OUTPUT_DIR}/eval",
                use_fast_impl=args.evaluation_type == "fast",
                nb_max_preds=cfg.TEST.DETECTIONS_PER_IMAGE,
            )
            cfg.DATASETS.TEST = (f"{args.dataset_name}_test",)
            model = Trainer.build_model(cfg)
            DetectionCheckpointer(model).load(f"{cfg.OUTPUT_DIR}/model_final.pth")
            Trainer.test(cfg, model, evaluator)
        else:
            LOGGER.info("Evaluation on the test set skipped")


##########
# Training
##########


def train(args: argparse.Namespace) -> None:
    r"""Launch distributed training by using Detecton2's `launch()` function

    Parameters
    ----------
    args : argparse.Namespace
        training script arguments, see :py:meth:`_parse_args()`
    """
    args.classes = ast.literal_eval(args.classes)

    machine_rank = args.hosts.index(args.current_host)
    LOGGER.info(f"Machine rank: {machine_rank}")
    master_addr = args.hosts[0]
    master_port = "55555"

    url = "auto" if len(args.hosts) == 1 else f"tcp://{master_addr}:{master_port}"
    LOGGER.info(f"Device URL: {url}")

    launch(
        _train_impl,
        num_gpus_per_machine=args.num_gpus,
        num_machines=len(args.hosts),
        dist_url=url,
        machine_rank=machine_rank,
        args=(args,),
    )


#############
# Script API
#############


def _parse_args() -> argparse.Namespace:
    r"""Define training script API according to the argument that are parsed from the CLI

    Returns
    -------
    argparse.Namespace
        training script arguments, execute $(python $thisfile --help) for detailed documentation
    """

    parser = argparse.ArgumentParser()

    # Pretrained model
    parser.add_argument(
        "--model-type",
        type=str,
        default="faster_rcnn",
        choices=["faster_rcnn", "retinanet"],
        metavar="MT",
        help=(
            "Type of architecture to be used for object detection; "
            "two options are supported: 'faster_rccn' and 'retinanet' "
            "(default: faster_rcnn)"
        ),
    )
    parser.add_argument(
        "--backbone",
        type=str,
        default="R_50_C4",
        choices=[
            "R_50_C4",
            "R_50_DC5",
            "R_50_FPN",
            "R_101_C4",
            "R_101_DC5",
            "R_101_FPN",
            "X_101_32x8d_FPN",
        ],
        metavar="B",
        help=(
            "Encoder backbone, how to read this field: "
            "R50 (RetinaNet-50), R100 (RetinaNet-100), X101 (ResNeXt-101); "
            "C4 (Use a ResNet conv4 backbone with conv5 head), "
            "DC5 (ResNet conv5 backbone with dilations in conv5) "
            "FPN (Use a FPN on top of resnet) ;"
            "Attention! Only some combinations are supported, please refer to the original doc "
            "(https://github.com/facebookresearch/detectron2/blob/master/MODEL_ZOO.md) "
            "(default: R_50_C4)"
        ),
    )
    parser.add_argument(
        "--lr-schedule",
        type=int,
        default=1,
        choices=[1, 3],
        metavar="LRS",
        help=(
            "Length of the training schedule, two values are supported: 1 or 3. "
            "1x = 16 images / it * 90,000 iterations in total with the LR reduced at 60k and 80k."
            "3x = 16 images / it * 270,000 iterations in total with the LR reduced at 210k and 250k"
            "(default: 1)"
        ),
    )
    # Hyper-parameters
    parser.add_argument(
        "--num-workers",
        type=int,
        default=2,
        metavar="NW",
        help="Number of workers used to by the data loader (default: 2)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=0.00025,
        metavar="LR",
        help="Base learning rate value (default: 0.00025)",
    )
    parser.add_argument(
        "--num-iter",
        type=int,
        default=1000,
        metavar="I",
        help="Maximum number of iterations (default: 1000)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        metavar="B",
        help="Number of images per batch across all machines (default: 16)",
    )
    parser.add_argument(
        "--num-rpn",
        type=int,
        default=100,
        metavar="R",
        help="Total number of RPN examples per image (default: 100)",
    )
    parser.add_argument(
        "--reg-loss-type",
        type=str,
        default="smooth_l1",
        choices=["smooth_l1", "giou"],
        metavar="RLT",
        help=("Loss type used for regression subnet " "(default: smooth_l1)"),
    )

    # RetinaNet Specific
    parser.add_argument(
        "--focal-loss-gamma",
        type=float,
        default=2.0,
        metavar="FLG",
        help="Focal loss gamma, used in RetinaNet (default: 2.0)",
    )
    parser.add_argument(
        "--focal-loss-alpha",
        type=float,
        default=0.25,
        metavar="FLA",
        help="Focal loss alpha, used in RetinaNet. It must be in [0.1,1] (default: 0.25)",
    )

    # Faster-RCNN Specific
    parser.add_argument(
        "--bbox-reg-loss-weight",
        type=float,
        default=1.0,
        help="Weight regression loss (default: 0.1)",
    )
    parser.add_argument(
        "--bbox-rpn-pos-fraction",
        type=float,
        default=0.5,
        help="Target fraction of foreground (positive) examples per RPN minibatch (default: 0.5)",
    )
    parser.add_argument(
        "--bbox-head-pos-fraction",
        type=float,
        default=0.25,
        help=(
            "Target fraction of RoI minibatch that is labeled foreground (i.e. class > 0) "
            "(default: 0.25)"
        ),
    )
    parser.add_argument(
        "--log-period",
        type=int,
        default=40,
        help="Occurence in number of iterations at which loss values are logged",
    )

    # Inference Parameters
    parser.add_argument(
        "--det-per-img",
        type=int,
        default=200,
        metavar="R",
        help="Maximum number of detections to return per image during inference (default: 200)",
    )
    parser.add_argument(
        "--nms-thr",
        type=float,
        default=0.5,
        metavar="NMS",
        help="If IoU is bigger than this value, only more confident pred is kept "
        "(default: 0.5)",
    )
    parser.add_argument(
        "--pred-thr",
        type=float,
        default=0.5,
        metavar="PT",
        help="Minimum confidence score to retain prediction (default: 0.5)",
    )
    parser.add_argument(
        "--evaluation-type",
        choices=["fast", "coco"],
        type=str,
        default=None,
        help=(
            "Evaluation to run on the test set after the training loop on the test. "
            "Valid options are: `fast` (Detectron2 boosted COCO eval) and "
            "`coco` (default COCO evaluation). "
            "This value is by default None, which means that no evaluation is executed"
        ),
    )

    # Mandatory parameters
    parser.add_argument(
        "--classes", type=str, metavar="C", help="List of classes of objects"
    )
    parser.add_argument(
        "--dataset-name", type=str, metavar="DS", help="Name of the dataset"
    )
    parser.add_argument(
        "--label-name",
        type=str,
        metavar="DS",
        help="Name of category of objects to detect (e.g. 'object')",
    )

    # Container Environment
    parser.add_argument("--model-dir", type=str, default=os.environ["SM_MODEL_DIR"])

    parser.add_argument(
        "--training-channel",
        type=str,
        default=os.environ["SM_CHANNEL_TRAINING"],
        help="Path folder that contains training images (File mode)",
    )
    parser.add_argument(
        "--validation-channel",
        type=str,
        default=os.environ["SM_CHANNEL_VALIDATION"],
        help="Path folder that contains validation images (File mode)",
    )
    parser.add_argument(
        "--test-channel",
        type=str,
        default=os.environ["SM_CHANNEL_TEST"],
        help=(
            "Path folder that contains test images, "
            "these are used to evaluate the model but not to drive hparam tuning"
        ),
    )
    parser.add_argument(
        "--annotation-channel",
        type=str,
        default=os.environ["SM_CHANNEL_ANNOTATION"],
        help="Path to folder that contains augumented manifest files with annotations",
    )

    parser.add_argument("--num-gpus", type=int, default=os.environ["SM_NUM_GPUS"])
    parser.add_argument(
        "--hosts", type=str, default=ast.literal_eval(os.environ["SM_HOSTS"])
    )
    parser.add_argument(
        "--current-host", type=str, default=os.environ["SM_CURRENT_HOST"]
    )
    return parser.parse_args()


if __name__ == "__main__":
    train(_parse_args())
