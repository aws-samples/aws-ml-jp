"""Run COCO evaluation on arbitrary number of predicted bounding boxes"""
import itertools
import os
import json
import copy
from typing import Tuple
import time

import numpy as np
from pycocotools.cocoeval import COCOeval
from detectron2 import _C
from detectron2.evaluation import COCOEvaluator
from detectron2.utils.file_io import PathManager


class EvaluateObjectDetection(COCOeval):
    r"""Run COCO evaluation on an arbitrary number of bounding boxes"""

    def summarize(self):
        """Compute and display summary metrics for evaluation results"""

        def _summarize(use_ap: bool, iou_thr=None, area_rng="all", max_dets=100):
            params = self.params
            out_str = (
                " {:<18} {} @[ IoU={:<9} | area={:>6s} | maxDets={:>3d} ] = {:0.3f}"
            )
            title_str = "Average Precision" if use_ap else "Average Recall"
            type_str = "(AP)" if use_ap else "(AR)"
            iou_str = (
                "{:0.2f}:{:0.2f}".format(params.iouThrs[0], params.iouThrs[-1])
                if iou_thr is None
                else "{:0.2f}".format(iou_thr)
            )

            aind = [i for i, aRng in enumerate(params.areaRngLbl) if aRng == area_rng]
            mind = [i for i, mDet in enumerate(params.maxDets) if mDet == max_dets]
            if use_ap:
                # dimension of precision: [TxRxKxAxM]
                metric_val = self.eval["precision"]
                # IoU
                if iou_thr is not None:
                    metric_id = np.where(iou_thr == params.iouThrs)[0]
                    metric_val = metric_val[metric_id]
                metric_val = metric_val[:, :, :, aind, mind]
            else:
                # dimension of recall: [TxKxAxM]
                metric_val = self.eval["recall"]
                if iou_thr is not None:
                    metric_id = np.where(iou_thr == params.iouThrs)[0]
                    metric_val = metric_val[metric_id]
                metric_val = metric_val[:, :, aind, mind]
            if len(metric_val[metric_val > -1]) == 0:
                mean_s = -1
            else:
                mean_s = np.mean(metric_val[metric_val > -1])
            print(
                out_str.format(title_str, type_str, iou_str, area_rng, max_dets, mean_s)
            )
            return mean_s

        def _summarize_detections():
            stats = np.zeros((12,))
            stats[0] = _summarize(True, max_dets=self.params.maxDets[0])
            stats[1] = _summarize(True, iou_thr=0.5, max_dets=self.params.maxDets[0])
            stats[2] = _summarize(True, iou_thr=0.75, max_dets=self.params.maxDets[0])
            stats[3] = _summarize(
                True, area_rng="small", max_dets=self.params.maxDets[0]
            )
            stats[4] = _summarize(
                True, area_rng="medium", max_dets=self.params.maxDets[0]
            )
            stats[5] = _summarize(
                True, area_rng="large", max_dets=self.params.maxDets[0]
            )
            stats[6] = _summarize(False, max_dets=self.params.maxDets[0])
            stats[9] = _summarize(
                False, area_rng="small", max_dets=self.params.maxDets[0]
            )
            stats[10] = _summarize(
                False, area_rng="medium", max_dets=self.params.maxDets[0]
            )
            stats[11] = _summarize(
                False, area_rng="large", max_dets=self.params.maxDets[0]
            )
            return stats

        if not self.eval:
            raise Exception("Please run accumulate() first")

        if self.params.iouType != "bbox":
            raise ValueError(
                f"{type(self).__name__} supports object detection evaluation only"
            )
        self.stats = _summarize_detections()


class FastEvaluateObjectDetection(EvaluateObjectDetection):
    r"""This class is the same as Detecron2's `COCOeval_opt`

    The only change is that this class inherits from `EvaluateObjectDetection` instead that from
    COCOeval
    """

    def evaluate(self):
        """
        Run per image evaluation on given images and store results in self.evalImgs_cpp, a
        datastructure that isn't readable from Python but is used by a c++ implementation of
        accumulate().  Unlike the original COCO PythonAPI, we don't populate the datastructure
        self.evalImgs because this datastructure is a computational bottleneck.
        :return: None
        """
        tic = time.time()

        print("Running per image evaluation...")
        params = self.params
        # add backward compatibility if useSegm is specified in params
        if params.useSegm is not None:
            params.iouType = "segm" if params.useSegm == 1 else "bbox"
            print(
                "useSegm (deprecated) is not None. Running {} evaluation".format(
                    params.iouType
                )
            )
        print("Evaluate annotation type *{}*".format(params.iouType))
        params.imgIds = list(np.unique(params.imgIds))
        if params.useCats:
            params.catIds = list(np.unique(params.catIds))
        params.maxDets = sorted(params.maxDets)
        self.params = params

        self._prepare()

        # loop through images, area range, max detection number
        cat_ids = params.catIds if params.useCats else [-1]

        if params.iouType == "segm" or params.iouType == "bbox":
            compute_IoU = self.computeIoU
        elif params.iouType == "keypoints":
            compute_IoU = self.computeOks
        else:
            assert False, f"Add implementation for {params.iouType}"
        self.ious = {
            (imgId, catId): compute_IoU(imgId, catId)
            for imgId in params.imgIds
            for catId in cat_ids
        }

        maxDet = params.maxDets[-1]

        # <<<< Beginning of code differences with original COCO API
        def convert_instances_to_cpp(instances, is_det=False):
            # Convert annotations for a list of instances in an image to a format that's fast
            # to access in C++
            instances_cpp = []
            for instance in instances:
                instance_cpp = _C.InstanceAnnotation(
                    int(instance["id"]),
                    instance["score"] if is_det else instance.get("score", 0.0),
                    instance["area"],
                    bool(instance.get("iscrowd", 0)),
                    bool(instance.get("ignore", 0)),
                )
                instances_cpp.append(instance_cpp)
            return instances_cpp

        # Convert GT annotations, detections, and IOUs to a format that's fast to access in C++
        ground_truth_instances = [
            [
                convert_instances_to_cpp(self._gts[imgId, catId])
                for catId in params.catIds
            ]
            for imgId in params.imgIds
        ]
        detected_instances = [
            [
                convert_instances_to_cpp(self._dts[imgId, catId], is_det=True)
                for catId in params.catIds
            ]
            for imgId in params.imgIds
        ]
        ious = [
            [self.ious[imgId, catId] for catId in cat_ids] for imgId in params.imgIds
        ]

        if not params.useCats:
            # For each image, flatten per-category lists into a single list
            ground_truth_instances = [
                [[o for c in i for o in c]] for i in ground_truth_instances
            ]
            detected_instances = [
                [[o for c in i for o in c]] for i in detected_instances
            ]

        # Call C++ implementation of self.evaluateImgs()
        self._evalImgs_cpp = _C.COCOevalEvaluateImages(
            params.areaRng,
            maxDet,
            params.iouThrs,
            ious,
            ground_truth_instances,
            detected_instances,
        )
        self._evalImgs = None

        self._paramsEval = copy.deepcopy(self.params)
        toc = time.time()
        print("COCOeval_opt.evaluate() finished in {:0.2f} seconds.".format(toc - tic))
        # >>>> End of code differences with original COCO API

    def accumulate(self):
        """
        Accumulate per image evaluation results and store the result in self.eval.  Does not
        support changing parameter settings from those used by self.evaluate()
        """
        print("Accumulating evaluation results...")
        tic = time.time()
        if not hasattr(self, "_evalImgs_cpp"):
            print("Please run evaluate() first")

        self.eval = _C.COCOevalAccumulate(self._paramsEval, self._evalImgs_cpp)

        # recall is num_iou_thresholds X num_categories X num_area_ranges X num_max_detections
        self.eval["recall"] = np.array(self.eval["recall"]).reshape(
            self.eval["counts"][:1] + self.eval["counts"][2:]
        )

        # precision and scores are num_iou_thresholds X num_recall_thresholds X num_categories X
        # num_area_ranges X num_max_detections
        self.eval["precision"] = np.array(self.eval["precision"]).reshape(
            self.eval["counts"]
        )
        self.eval["scores"] = np.array(self.eval["scores"]).reshape(self.eval["counts"])
        toc = time.time()
        print(
            "COCOeval_opt.accumulate() finished in {:0.2f} seconds.".format(toc - tic)
        )


class D2CocoEvaluator(COCOEvaluator):
    r"""Detectron2 COCO evaluator that allows setting the maximum number of detections"""

    def __init__(
        self,
        dataset_name: str,
        tasks: Tuple[str, ...],
        distributed: bool,
        output_dir: str,
        use_fast_impl: bool,
        nb_max_preds: int,
    ):
        super().__init__(
            dataset_name=dataset_name,
            tasks=tasks,
            distributed=distributed,
            output_dir=output_dir,
            use_fast_impl=use_fast_impl,
        )
        self._nb_max_preds = nb_max_preds

    def _eval_predictions(self, predictions, img_ids=None):
        """
        Evaluate predictions on the given tasks.
        Fill self._results with the metrics of the tasks.
        """
        self._logger.info("Preparing results for COCO format ...")
        coco_results = list(itertools.chain(*[x["instances"] for x in predictions]))
        tasks = self._tasks or self._tasks_from_predictions(coco_results)

        # unmap the category ids for COCO
        if hasattr(self._metadata, "thing_dataset_id_to_contiguous_id"):
            dataset_id_to_contiguous_id = self._metadata.thing_dataset_id_to_contiguous_id
            all_contiguous_ids = list(dataset_id_to_contiguous_id.values())
            num_classes = len(all_contiguous_ids)
            assert min(all_contiguous_ids) == 0 and max(all_contiguous_ids) == num_classes - 1

            reverse_id_mapping = {v: k for k, v in dataset_id_to_contiguous_id.items()}
            for result in coco_results:
                category_id = result["category_id"]
                assert category_id < num_classes, (
                    f"A prediction has class={category_id}, "
                    f"but the dataset only has {num_classes} classes and "
                    f"predicted class id should be in [0, {num_classes - 1}]."
                )
                result["category_id"] = reverse_id_mapping[category_id]

        if self._output_dir:
            file_path = os.path.join(self._output_dir, "coco_instances_results.json")
            self._logger.info("Saving results to {}".format(file_path))
            with PathManager.open(file_path, "w") as f:
                f.write(json.dumps(coco_results))
                f.flush()

        if not self._do_evaluation:
            self._logger.info("Annotations are not available for evaluation.")
            return

        self._logger.info(
            "Evaluating predictions with {} COCO API...".format(
                "unofficial" if self._use_fast_impl else "official"
            )
        )
        for task in sorted(tasks):
            assert task in {"bbox", "segm", "keypoints"}, f"Got unknown task: {task}!"
            coco_eval = (
                _evaluate_on_coco_impl(
                    self._coco_api,
                    coco_results,
                    task,
                    max_nb_preds=self._nb_max_preds,
                    kpt_oks_sigmas=self._kpt_oks_sigmas,
                    use_fast_impl=self._use_fast_impl,
                    img_ids=img_ids,
                )
                if len(coco_results) > 0
                else None  # cocoapi does not handle empty results very well
            )

            res = self._derive_coco_results(
                coco_eval, task, class_names=self._metadata.get("thing_classes")
            )
            self._results[task] = res


def _evaluate_on_coco_impl(
    coco_gt,
    coco_results,
    iou_type,
    max_nb_preds,
    kpt_oks_sigmas=None,
    use_fast_impl=True,
    img_ids=None,
):
    """
    Evaluate the coco results using COCOEval API.
    """
    assert len(coco_results) > 0

    if iou_type == "segm":
        coco_results = copy.deepcopy(coco_results)
        # When evaluating mask AP, if the results contain bbox, cocoapi will
        # use the box area as the area of the instance, instead of the mask area.
        # This leads to a different definition of small/medium/large.
        # We remove the bbox field to let mask AP use mask area.
        for c in coco_results:
            c.pop("bbox", None)

    coco_dt = coco_gt.loadRes(coco_results)
    coco_eval = (
        FastEvaluateObjectDetection if use_fast_impl else EvaluateObjectDetection
    )(coco_gt, coco_dt, iou_type)
    coco_eval.params.maxDets = [max_nb_preds]
    if img_ids is not None:
        coco_eval.params.imgIds = img_ids

    if iou_type == "keypoints":
        # Use the COCO default keypoint OKS sigmas unless overrides are specified
        if kpt_oks_sigmas:
            assert hasattr(
                coco_eval.params, "kpt_oks_sigmas"
            ), "pycocotools is too old!"
            coco_eval.params.kpt_oks_sigmas = np.array(kpt_oks_sigmas)
        # COCOAPI requires every detection and every gt to have keypoints, so
        # we just take the first entry from both
        num_keypoints_dt = len(coco_results[0]["keypoints"]) // 3
        num_keypoints_gt = len(next(iter(coco_gt.anns.values()))["keypoints"]) // 3
        num_keypoints_oks = len(coco_eval.params.kpt_oks_sigmas)
        assert num_keypoints_oks == num_keypoints_dt == num_keypoints_gt, (
            f"[COCOEvaluator] Prediction contain {num_keypoints_dt} keypoints. "
            f"Ground truth contains {num_keypoints_gt} keypoints. "
            f"The length of cfg.TEST.KEYPOINT_OKS_SIGMAS is {num_keypoints_oks}. "
            "They have to agree with each other. For meaning of OKS, please refer to "
            "http://cocodataset.org/#keypoints-eval."
        )

    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()

    return coco_eval
