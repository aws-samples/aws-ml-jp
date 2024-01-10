import os
from pathlib import Path
import logging
from logging import getLogger
import urllib.request
import json
import shutil
import random


def prepare_scripts(logger: logging.Logger = None) -> Path:
    logger.info("Copy fine tuning code from the fine-tuning/instruction-tuning.")
    target_path = Path(os.path.dirname(__file__)).joinpath("scripts")
    source_path = target_path.parent.parent.parent.joinpath(
        "fine-tuning/instruction-tuning/Transformers/scripts"
    )
    if target_path.exists() and target_path.is_dir():
        logger.info("\tDelete existing scripts folder.")
        shutil.rmtree(target_path)
    shutil.copytree(source_path, target_path)
    return target_path


def prepare_dataset(
    data_dir: str = "data", logger: logging.Logger = None
) -> dict[str, Path]:
    logger.info(f"Prepare JSQuAD dataset to {data_dir}.")
    base_url = "https://github.com/yahoojapan/JGLUE/raw/main/datasets/jsquad-v1.1/"
    train_raw_file_name = "train-v1.1.json"
    valid_raw_file_name = "valid-v1.1.json"

    data_path = Path(os.path.dirname(__file__)).joinpath(data_dir)

    if data_path.exists():
        shutil.rmtree(data_path)
    data_path.mkdir()

    paths = {"train": train_raw_file_name, "valid": valid_raw_file_name}
    for file_kind in paths:
        file_name = paths[file_kind]
        logger.info(f"\tDownload {file_name}.")
        file_path = data_path.joinpath(file_name)
        with file_path.open(mode="wb") as f:
            f.write(urllib.request.urlopen(f"{base_url}{file_name}").read())

        paths[file_kind] = file_path

    return paths


def convert_to_instruction_format(
    path: Path, logger: logging.Logger = None
) -> list[dict]:
    logger.info(f"Convert {path.name} to instruction format.")

    with path.open() as f:
        raw_data = json.loads(f.read())

    question_answers = []
    logger.info(f"\tThere are {len(raw_data['data'])} titles (samples).")
    for title_index, title in enumerate(raw_data["data"]):
        for paragraph_index, paragraph in enumerate(title["paragraphs"]):
            context = paragraph["context"]
            for question_index, question in enumerate(paragraph["qas"]):
                instruction = question["question"]
                answer = question["answers"][0]["text"]
                answer_start = question["answers"][0]["answer_start"]
                question_id = question["id"]
                qa = {
                    "title_index": title_index,
                    "paragraph_index": paragraph_index,
                    "question_index": question_index,
                    "question_id": question_id,
                    "input": context,
                    "instruction": instruction,
                    "output": answer,
                    "output_start": answer_start
                }
                question_answers.append(qa)

    return question_answers


def save_splitted_instruction_data(
    train_data_path: Path,
    instructions: list[dict],
    initial_data_sizes: list[int],
    max_question_index: int = 5,
    logger: logging.Logger = None,
) -> list[Path]:
    instruction_all = []
    data_dir = train_data_path.parent
    logger.info(f"Split {len(instructions)} instruction data.")
    for question_index in range(max_question_index):
        for instruction in instructions:
            if instruction["question_index"] == question_index:
                instruction_all.append(instruction)

        # create lower size dataset from question_index == 0 dataset to avoid duplicate context
        if question_index == 0:
            for data_size in initial_data_sizes:
                samples = random.sample(instruction_all, data_size)
                with data_dir.joinpath(f"jsquad-{str(data_size).zfill(5)}.json").open(
                    mode="w"
                ) as f:
                    f.write(json.dumps(samples))
                logger.info(f"\t {data_size} data is saved.")

        num_current_instructions = len(instruction_all)
        with data_dir.joinpath(
            f"jsquad-{str(num_current_instructions).zfill(5)}.json"
        ).open(mode="w") as f:
            f.write(json.dumps(instruction_all))
        logger.info(f"\t {num_current_instructions} data is saved.")

    jsquad_file_paths = sorted(data_dir.glob("jsquad-*.json"))
    return jsquad_file_paths


if __name__ == "__main__":
    log_level = logging.DEBUG
    logger = getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(level=log_level)
    logger.setLevel(level=log_level)
    logger.addHandler(handler)

    prepare_scripts(logger=logger)
    file_paths = prepare_dataset(logger=logger)
    train_data_path = file_paths["train"]
    train_instruction_data = convert_to_instruction_format(
        train_data_path, logger=logger
    )
    initial_data_sizes = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
    jsquad_file_paths = save_splitted_instruction_data(
        train_data_path, train_instruction_data, initial_data_sizes, logger=logger
    )
    logger.info(f"{len(jsquad_file_paths)} files are created.")
    for path in jsquad_file_paths:
        logger.info(f"\t{path.name}")
    logger.info(f"Show one sample of data : {json.dumps(train_instruction_data[0], indent=4, ensure_ascii=False)}")
