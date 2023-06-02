import os, json, torch
from rwkv.model import RWKV
from rwkv.utils import PIPELINE, PIPELINE_ARGS
os.environ['RWKV_JIT_ON'] = '1'
os.environ["RWKV_CUDA_ON"] = '0'

def generate_prompt(instruction, input):
    if input != "":
        return f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.
# Instruction:
{instruction}
# Input:
{input}
# Response:
"""
    else:
        return f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.
# Instruction:
{instruction}
# Response:
"""
    
def merge_lora(
    use_gpu: bool = True,
    lora_alpha: int = 32,
    base_model: str = "",
    lora: str = "",
    output: str = "",
):
    # Original: https://github.com/Blealtan/RWKV-LM-LoRA/blob/main/RWKV-v4neo/merge_lora.py
    from collections import OrderedDict
    import sys
    from typing import Dict
    import typing
    
    device = 'cuda' if use_gpu else 'cpu'

    with torch.no_grad():
        w: Dict[str, torch.Tensor] = torch.load(base_model, map_location=device)
        # merge LoRA-only slim checkpoint into the main weights
        w_lora: Dict[str, torch.Tensor] = torch.load(lora, map_location=device)
        for k in w_lora.keys():
            w[k] = w_lora[k]
        output_w: typing.OrderedDict[str, torch.Tensor] = OrderedDict()
        # merge LoRA weights
        keys = list(w.keys())
        for k in keys:
            if k.endswith('.weight'):
                prefix = k[:-len('.weight')]
                lora_A = prefix + '.lora_A'
                lora_B = prefix + '.lora_B'
                if lora_A in keys:
                    assert lora_B in keys
                    print(f'merging {lora_A} and {lora_B} into {k}')
                    assert w[lora_B].shape[1] == w[lora_A].shape[0]
                    lora_r = w[lora_B].shape[1]
                    w[k] = w[k].to(device=device)
                    w[lora_A] = w[lora_A].to(device=device)
                    w[lora_B] = w[lora_B].to(device=device)
                    w[k] += w[lora_B] @ w[lora_A] * (lora_alpha / lora_r)
                    output_w[k] = w[k].to(device='cpu', copy=True)
                    del w[k]
                    del w[lora_A]
                    del w[lora_B]
                    continue

            if 'lora' not in k:
                print(f'retaining {k}')
                output_w[k] = w[k].clone()
                del w[k]

        torch.save(output_w, output)

def load_model(
    model_path: str = "",
    model_url: str = "", # Optional: if model is packaged, it is not required
    tokenizer_path: str = "",
    strategy: str = "",
    lora: str = "",
    lora_alpha: int = 32
):
    print(model_path, model_url, tokenizer_path, strategy)
    
    # Download Model if not exist
    if model_url and not os.path.exists(model_path):
        import urllib.request
        print(f"Downloading model from {model_url} this may take a while")
        urllib.request.urlretrieve(model_url, model_path)
        
    # Merge LoRA weights if exist
    if lora:
        print("Merging LoRA weights...")
        output_path = "/tmp/merged.pth"
        merge_lora(
            use_gpu = torch.cuda.is_available(),
            lora_alpha = lora_alpha,
            base_model = model_path,
            lora = lora,
            output = output_path,
        )
        model_path = output_path
    
    print("Loading Model...")
    model = RWKV(model=model_path, strategy=strategy)
    pipeline = PIPELINE(model, tokenizer_path)
    
    return pipeline
    
    
def evaluate(
    model_objects,
    instruction,
    input=None,
    temperature=0.1,
    top_p=0.75,
    top_k=40,
    num_beams=4,
    token_count=200,
    **kwargs,
):
    pipeline = model_objects
    
    args = PIPELINE_ARGS(
        temperature = temperature,
        top_p = top_p, 
        top_k = top_k, 
        # alpha_frequency = 0.25, 
        # alpha_presence = 0.25, 
        # token_ban = [],
        # token_stop = [0],
        # chunk_len = 256
        **kwargs
    ) 
    
    prompt = generate_prompt(instruction, input)
    
    result = pipeline.generate(prompt, token_count=token_count, args=args)
    
    return result

    
def model_fn(
    model_dir
):
    model_params = json.loads(os.environ['model_params'])
    
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
        return evaluate(
            model_objects=model,
            **data
        )
    except Exception as e:
        print("Inference error: ", e)
        
