import os, json
from typing import Union

import ctranslate2
import transformers
import torch

class Prompter(object):

    def __init__(self, prompt_input: str = "", prompt_no_input: str = ""):
        self.template = {
            "prompt_input": prompt_input,
            "prompt_no_input": prompt_no_input
        }

    def generate_prompt(
        self,
        instruction: str,
        input: Union[None, str] = None,
        label: Union[None, str] = None,
    ) -> str:
        if input:
            res = self.template["prompt_input"].format(
                instruction=instruction, input=input
            )
        else:
            res = self.template["prompt_no_input"].format(
                instruction=instruction
            )
        return res

    
def load_model(
    tokenizer: str = "",
    model: str = "",
    prompt_input: str = "",
    prompt_no_input: str = "",
    **kwargs,
):
    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"

    generator = ctranslate2.Generator(model, device=device)
    tokenizer = transformers.AutoTokenizer.from_pretrained(tokenizer)
    prompter = Prompter(prompt_input, prompt_no_input)

    return tokenizer, generator, prompter


def inference(
    model_objects,
    instruction=None,
    input=None,
    max_new_tokens=128,
    stop_ids=[],
    **kwargs,
):
    tokenizer, generator, prompter = model_objects
    
    if instruction != "":
        prompt = prompter.generate_prompt(instruction, input)
    else:
        prompt = input
    
    tokens = tokenizer.convert_ids_to_tokens(
        tokenizer.encode(
            prompt,
            add_special_tokens=False,
        )
    )

    results = generator.generate_batch(
        [tokens],
        max_length=max_new_tokens,
        include_prompt_in_result=False,
        end_token=stop_ids,
        **kwargs
    )

    text = tokenizer.decode(results[0].sequences_ids[0])
    return text


def model_fn(
    model_dir
):
    model_params = json.loads(os.environ['model_params'])
    print(model_params)
    try:
        return load_model(**model_params)
    except Exception as e:
        print("Model error:", e)


def input_fn(input_data, content_type):
    print(input_data, content_type)
    if content_type == "application/json":
        input_data = json.loads(input_data)
    return input_data


def predict_fn(
    data,
    model
):
    print("Predict Fn")
    print(data)
    try:
        return inference(
            model_objects=model,
            **data
        )
    except Exception as e:
        print("Inference error: ", e)

