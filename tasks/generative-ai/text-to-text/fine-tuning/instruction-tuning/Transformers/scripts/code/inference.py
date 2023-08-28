import os
import sys
import json
from typing import Dict

import torch
import transformers
from peft import PeftModel
from transformers import GenerationConfig, AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList, BitsAndBytesConfig
import deepspeed

from utils.prompter import Prompter


class StopOnTokens(StoppingCriteria):
    def __init__(self, stop_ids):
        self.stop_ids = stop_ids

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        for stop_id in self.stop_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False


def main(
    load_8bit: bool = False,
    load_4bit: bool = False,  # If 8 bit is also specified, 4 bit has priority
    use_deepspeed: bool = False,
    use_optimum: bool = False,
    base_model: str = "",
    tokenizer_name: str = "",
    peft: bool = True,
    lora_weights: str = "tloen/alpaca-lora-7b",
    prompt_template: str = "",
    tokenizer_kwargs: Dict[str, any] = {},
    **kwargs,
):
    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    print("Device: ", device)
    print("Device Count: ", torch.cuda.device_count())

    base_model = base_model or os.environ.get("BASE_MODEL", "")
    assert (base_model), "Please specify a --base_model"
    tokenizer_name = tokenizer_name or base_model

    prompter = Prompter(prompt_template)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, **tokenizer_kwargs)

    print("Loading Model: ", base_model)
    if device == "cuda":
        if load_4bit:
            nf4_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.bfloat16
            )
            model = AutoModelForCausalLM.from_pretrained(
                base_model,
                quantization_config=nf4_config,
                device_map="auto",
                cache_dir="/tmp/model_cache/",
                **kwargs
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                base_model,
                load_in_8bit=load_8bit,
                torch_dtype=torch.float16,
                device_map="auto",
                cache_dir="/tmp/model_cache/",
                **kwargs
            )

        model.model_parallel = False  # For MPT patch compatibility

        if peft:
            print("Loading Lora Weight")
            model = PeftModel.from_pretrained(
                model,
                lora_weights,
                torch_dtype=torch.float16,
            )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            base_model, device_map={"": device}, low_cpu_mem_usage=True
        )
        if peft:
            model = PeftModel.from_pretrained(
                model,
                lora_weights,
                device_map={"": device},
            )
    print("Model Loaded")

    if not (load_8bit or load_4bit):
        model.half()  # seems to fix bugs for some users.

    model.eval()
    
    if use_deepspeed:
        ds_engine = deepspeed.init_inference(
            model,
            mp_size=torch.cuda.device_count(),
            dtype=torch.float16,
            replace_method='auto'
        )
        model = ds_engine.module
    
    if torch.__version__ >= "2" and sys.platform != "win32":
        if use_optimum:
            model = model.to_bettertransformer()
        model = torch.compile(model)

    return device, prompter, tokenizer, model


def evaluate(
    model_objects,
    instruction=None,
    input=None,
    max_new_tokens=128,
    stop_ids=[],
    **kwargs,
):
    device, prompter, tokenizer, model = model_objects

    # Generate Prompt when there are instruction, otherwise use input
    if instruction != "":
        prompt = prompter.generate_prompt(instruction, input)
    else:
        prompt = input
    inputs = tokenizer(
        prompt, 
        add_special_tokens=False,
        return_token_type_ids=False,
        return_tensors="pt"
    ).to(device)

    generation_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        return_dict_in_generate=True,
        output_scores=True,
        **kwargs,
    )
    with torch.no_grad():
        generation_output = model.generate(
            **inputs,
            generation_config=generation_config,
            stopping_criteria=StoppingCriteriaList([StopOnTokens(stop_ids)]),
        )
    s = generation_output.sequences[0, inputs['input_ids'].size(1):]
    output = tokenizer.decode(s, skip_special_tokens=True)
    return output


def model_fn(
    model_dir
):
    model_params = json.loads(os.environ['model_params'])
    print(model_params)
    try:
        return main(**model_params)
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
        return evaluate(
            model_objects=model,
            **data
        )
    except Exception as e:
        print("Inference error: ", e)