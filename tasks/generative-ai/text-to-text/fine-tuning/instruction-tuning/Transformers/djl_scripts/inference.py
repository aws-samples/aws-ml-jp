from djl_python import Input, Output
import os
import torch
from peft import PeftModel
from transformers import GenerationConfig, AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList, BitsAndBytesConfig
from typing import Any, Dict, Tuple, Union, Optional
import warnings

model = None
tokenizer = None
prompter = None


class StopOnTokens(StoppingCriteria):
    def __init__(self, stop_ids):
        self.stop_ids = stop_ids

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        for stop_id in self.stop_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False

    
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
    
    
def get_model(properties):
    # Get Properties
    print(properties)
    model_name = properties["model_id"]
    prompt_input = properties.get("prompt_input", "")
    prompt_no_input = properties.get("prompt_no_input", "")
    lora_weights = properties.get("lora_weights", "")
    load_8bit = properties.get("load_8bit", False)
    load_4bit = properties.get("load_4bit", False)
    
    if load_4bit:
        nf4_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=nf4_config,
            device_map="auto",
            cache_dir="/tmp/model_cache/",
            trust_remote_code=True,
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            load_in_8bit=load_8bit,
            torch_dtype=torch.float16,
            device_map="auto",
            cache_dir="/tmp/model_cache/",
            trust_remote_code=True,
        )
    if lora_weights:
        print("Loading Lora Weight from: ", os.getcwd(), os.listdir(lora_weights), lora_weights)
        model = PeftModel.from_pretrained(
            model,
            lora_weights,
            torch_dtype=torch.float16,
            device_map="auto",
        )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    prompter = Prompter(prompt_input, prompt_no_input)
    return model, tokenizer, prompter


def handle(inputs: Input) -> Optional[Output]:
    global model
    global tokenizer
    global prompter
    
    if not model:
        try:
            model, tokenizer, prompter = get_model(inputs.get_properties())
        except Exception as e:
            print(e)
            
    if inputs.is_empty():
        # Model server makes an empty call to warmup the model on startup
        return None
    
    data = inputs.get_as_json()
    instruction = data["instruction"]
    input = data["input"]
    if instruction != "":
        prompt = prompter.generate_prompt(instruction, input)
    else:
        prompt = input
    print(prompt)
    
    generation_kwargs = data["properties"]
    stop_ids = data.get("stop_ids", [])
    
    inputs = tokenizer(
        prompt, 
        add_special_tokens=False,
        return_token_type_ids=False,
        return_tensors="pt"
    ).to(model.device)
    generation_config = GenerationConfig(
        return_dict_in_generate=True,
        output_scores=True,
        **generation_kwargs,
    )
    with torch.no_grad():
        generation_output = model.generate(
            **inputs,
            generation_config=generation_config,
            stopping_criteria=StoppingCriteriaList([StopOnTokens(stop_ids)]),
        )
    s = generation_output.sequences[0, inputs['input_ids'].size(1):]
    output = tokenizer.decode(s, skip_special_tokens=True)
    
    return Output().add_as_json(output)
