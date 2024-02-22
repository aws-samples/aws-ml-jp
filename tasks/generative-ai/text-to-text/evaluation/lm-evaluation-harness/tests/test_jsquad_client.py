import json
import random
from pathlib import Path
import boto3
import pytest
from jsquad_client import JSQuADClaude


@pytest.fixture
def s3_bucket():
    s3 = boto3.client("s3")
    bucket_name = "jsquad.client.test.aws.ml.jp"
    s3.create_bucket(Bucket=bucket_name)
    yield bucket_name

    response = s3.list_objects(Bucket=bucket_name)
    if "Contents" in response:
        for _object in response["Contents"]:
            s3.delete_object(Bucket=bucket_name, Key=_object["Key"])
    s3.delete_bucket(Bucket=bucket_name)


class TestJSQuADClaude:
    def _sample(self) -> dict:
        path = Path(__file__).parent.joinpath("data/jsquad-samples.json")
        if not path.exists():
            raise Exception("Sample file does not exist.")

        with path.open() as f:
            samples = json.load(f)

        sample = random.choice(samples)
        return sample

    def test_prompt(self):
        prompter = JSQuADClaude()
        sample = self._sample()
        prompt = prompter.doc_to_text(sample)
        assert sample["input"].split("[SEP]")[-1].strip() in prompt
        assert sample["instruction"] in prompt

    def test_prompt_with_examples(self):
        prompter = JSQuADClaude()
        sample = self._sample()
        num_examples = 2
        examples = [self._sample() for i in range(num_examples)]
        prompt = prompter.doc_to_text(sample, examples)
        assert sample["input"].split("[SEP]")[-1].strip() in prompt
        assert sample["instruction"] in prompt
        print(prompt)
        assert prompt.count("<example>") == num_examples
        assert prompt.count("</example>") == num_examples
        assert False

    def test_answer(self):
        # Extract sample
        prompter = JSQuADClaude()
        sample = self._sample()

        # Generate answer
        prompt = prompter.doc_to_text(sample)
        answer = prompter.ask(prompt, prompter.choose_model(version="2.1")).strip()

        # Evaluate answer
        print(f"Claude answered {answer} and actual answer is {sample['output']}.")
        result = prompter.compute(sample, answer)

        # 1. compare with cold answer
        gold = prompter.compute(sample, sample["output"])
        assert gold["exact_match"] == 100.0
        assert gold["f1"] == 100.0

        # 2. compare with generate answer
        if answer == sample["output"]:
            assert result["exact_match"] == 100.0
        elif sample["output"] in answer:
            assert result["f1"] > 1

        # Compute scores of multiple samples
        sample_2 = self._sample()
        prompt_2 = prompter.doc_to_text(sample_2)
        answer_2 = prompter.ask(prompt_2, prompter.choose_model(version="2.1")).strip()
        result_multiple = prompter.compute([sample, sample_2], [answer, answer_2])

        if answer == sample["output"] and answer_2 == sample_2["output"]:
            assert result_multiple["exact_match"] == 100.0
        elif answer == sample["output"] or answer_2 == sample_2["output"]:
            assert result_multiple["exact_match"] == 50.0
        else:
            assert result_multiple["exact_match"] == 0.0

    def test_answer_with_examples(self):
        prompter = JSQuADClaude()
        num_examples = 3
        examples = [self._sample() for i in range(num_examples)]
        sample = examples[0]
        examples = examples[1:]

        # Generate answer
        prompt = prompter.doc_to_text(sample, examples)
        answer = prompter.ask(prompt, prompter.choose_model(version="2.1")).strip()

        # Evaluate answer
        print(f"Claude answered {answer} and actual answer is {sample['output']}.")
        result = prompter.compute(sample, answer)

        if answer == sample["output"]:
            assert result["exact_match"] == 100.0
        elif sample["output"] in answer:
            assert result["f1"] > 1

    def test_answer_batch(self, s3_bucket):
        # Extract sample
        prompter = JSQuADClaude()
        num_sample = 3
        prompts = [prompter.doc_to_text(self._sample()) for i in range(num_sample)]

        # Batch inference
        answers = prompter.ask_batch(
            bucket_name=s3_bucket,
            prompts=prompts,
            model_id=prompter.choose_model(version="1", instant=True),
        )

        assert len(answers) == 3
