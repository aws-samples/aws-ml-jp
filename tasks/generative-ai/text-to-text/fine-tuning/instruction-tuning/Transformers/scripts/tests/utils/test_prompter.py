import unittest
from code.utils.prompter import Prompter


class TestPrompter():
    
    def test_generate_prompt_with_input(self):
        prompter = Prompter(template_name="simple_qa", verbose=True)
        instruction = "Please answer the following question."
        _input = "Where is the capital of Japan?"
        label = "Tokyo"
        prompt = prompter.generate_prompt(
            instruction=instruction,
            input=_input,
            label=label
        )
        
        expected = f"Question:\n{instruction}\n\nContext:\n{_input}\n\nAnswer:\n{label}"
        assert expected == prompt, "Prompt does not match the expected one"

    def test_generate_prompt_without_input(self):
        prompter = Prompter(template_name="simple_qa", verbose=True)
        instruction = "Please answer the following question."
        label = "Tokyo"
        prompt = prompter.generate_prompt(
            instruction=instruction,
            label=label
        )
        
        expected = f"Question:\n{instruction}\n\nAnswer:\n{label}"
        assert expected == prompt, "Prompt does not match the expected one"

    def test_get_response(self):
        prompter = Prompter(template_name="simple_qa", verbose=True)
        instruction = "Please answer the following question."
        label = "Tokyo"
        prompt = prompter.generate_prompt(
            instruction=instruction,
            label=label
        )
        
        assert label == prompter.get_response(prompt), "Label does not match the expected one"
