import argparse
from pathlib import Path
import re
import json
import logging
from logging import getLogger

import boto3
from jsquad_preparation import convert_to_instruction_format
from jsquad_client import JSQuADClaude


def main(
        bucket_name: str,
        dataset_size: int = 8,
        version: str = "2.1",
        instant=False,
        max_length: int = 1024,
        temperature: float = 0.0,
        top_p: float = 0.99,
        validation_limit: int = -1,
        logger: logging.Logger = None):
    # Prepare training dataset
    DATA_DIR = Path(__file__).parent.joinpath("data")
    training_file_all = DATA_DIR.glob("jsquad-*.json")
    training_file = None

    if dataset_size > 0:
        for file in training_file_all:
            size = int(re.search(r"\d+", file.name).group())
            if size == dataset_size:
                training_file = file

        if training_file is None:
            raise Exception(f"Cannot find out training data for size {dataset_size}")
        else:
            logger.info(f"Training data set size: {size}.")
    else:
        training_file = DATA_DIR.joinpath("jsquad-00000.json")
        logger.info("Do not use training data.")

    # Prepare validation dataset
    validation_file = DATA_DIR.joinpath("valid-v1.1.json")
    validation_data = convert_to_instruction_format(validation_file, logger=logger)
    logger.info(f"Validation data set size: {len(validation_data)}.")
    if validation_limit > 0:
        validation_data = validation_data[:validation_limit]
        logger.info(f"\t Limit validation data size to {validation_limit}.")

    # Create prompt
    logger.info("Create prompt by using training data.")
    client = JSQuADClaude()
    samples = []
    if dataset_size > 0:
        with training_file.open() as f:
            samples = json.load(f)

    prompts = [client.doc_to_text(doc, samples=samples) for doc in validation_data]

    # Generate answers
    logger.info("Generate answers by using Amazon Bedrock. It will take a long time...")
    answers = client.ask_batch(
        bucket_name=bucket_name,
        prompts=prompts,
        model_id=client.choose_model(version, instant),
        max_length=max_length,
        temperature=temperature,
        top_p=top_p,
        id_prefix=training_file.stem,
        logger=logger
    )

    # Compute score
    score = client.compute(validation_data, answers)
    if not DATA_DIR.joinpath("result").exists():
        DATA_DIR.joinpath("result").mkdir()
    
    with DATA_DIR.joinpath(f"result/answer-{training_file.name}").open("w") as f:
        for answer, actual in zip(answers, validation_data):
            f.write(f"{answer}\t{actual['output']}\n")
    
    result = {}
    result["version"] = version
    result["instant"] = instant
    result["dataset_size"] = dataset_size
    result["validation-limit"] = validation_limit
    result["max_length"] = max_length
    result["temperature"] = temperature
    result["top_p"] = top_p
    result["score"] = score 
    DATA_DIR.joinpath(f"result/score-{training_file.name}").write_text(json.dumps(result))    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute evaluation of Claude.")

    bucket_name = "bedrock.jsquad.client.aws.ml.jp"
    parser.add_argument("-b", "--bucket-name", default=bucket_name)
    parser.add_argument("-v", "--version", default="2.1")
    parser.add_argument("-i", "--instant", action="store_const", default=False)
    parser.add_argument("-ds", "--dataset-size", type=int, default=0)
    parser.add_argument("-limit", "--validation-limit", type=int, default=-1)
    parser.add_argument("-len", "--max-length", type=int, default=1024)
    parser.add_argument("-t", "--temperature", type=float, default=0.0)
    parser.add_argument("-p", "--top-p", type=float, default=0.99)

    log_level = logging.DEBUG
    logger = getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(level=log_level)
    logger.setLevel(level=log_level)
    logger.addHandler(handler)

    args = parser.parse_args()
    
    bucket_name = args.bucket_name
    s3 = boto3.resource('s3')
    if s3.Bucket(bucket_name) not in s3.buckets.all():
        s3.create_bucket(Bucket=bucket_name)

    main(
        bucket_name=bucket_name,
        version=args.version,
        instant=args.instant,
        dataset_size=args.dataset_size,
        validation_limit=args.validation_limit,
        max_length=args.max_length,
        temperature=args.temperature,
        top_p = args.top_p,
        logger=logger)
