import unittest
import json
import random
from pathlib import Path
from jsquad_prompt_tuning_evaluation import JSQuADClaude
from jsquad_prompt_tuning_evaluation import Bedrock


class TestJSQuADClaude(unittest.TestCase):

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


    def test_answer(self):
        prompter = JSQuADClaude()
        sample = self._sample()
        prompt = prompter.doc_to_text(sample)

        bedrock = Bedrock()
        answer = bedrock.ask_to_claude(prompt, version="2.1").strip()
        print(prompt)
        print(f"Claude answered {answer} and actual answer is {sample['output']}.")
        result = prompter.compute(sample, answer)
        gold = prompter.compute(sample, sample['output'])
        assert gold["exact_match"] == 100.0
        assert gold["f1"] == 100.0

        print(result)
        if answer == sample['output']:
            assert result["exact_match"] == 100.0
        elif sample['output'] in answer:
            assert result["f1"] > 1

        sample_2 = self._sample()
        prompt_2 = prompter.doc_to_text(sample_2)
        answer_2 = bedrock.ask_to_claude(prompt_2, version="2.1").strip()
        result_multiple = prompter.compute(
            [sample, sample_2],
            [answer, answer_2])

        if answer == sample['output'] and answer_2 == sample_2['output']:
            assert result_multiple["exact_match"] == 100.0
        elif answer == sample['output'] or answer_2 == sample_2['output']:
            assert result_multiple["exact_match"] == 50.0
        else:
            assert result_multiple["exact_match"] == 0.0

        print(result_multiple)


if __name__ == "__main__":
    unittest.main()
