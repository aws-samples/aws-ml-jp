# LLM Instruction Tuning on SageMaker

This project contains sample Notebooks to fine-tune / deploy Large Language Models (LLMs) on SageMaker.

There are three types of notebooks.

- `*_Inference.ipynb`: deploy pretrained model
- `*_Finetune.ipynb`: finetune normally and deploy the model
- `*_LoRA.ipynb`: finetune using LoRA method and deploy the model

Models are standardized to accept json with following format for ease of use.

```
[
    {
        "input": "",
        "instruction": "",
        "output": ""
    },
    ...
]
```

## List of Notebooks

| Noteobok | Description |
| -------- | ----------- |
| [Alpaca_LoRA.ipynb](AutoModel/Alpaca_LoRA.ipynb) | Finetuning and deploying Alpaca-LoRA with Alpaca Dataset |
| [Alpaca_Inference.ipynb](AutoModel/Alpaca_Inference.ipynb) | Deploy pre-trained Alpaca-LoRA |
| [Alpaca_LoRA_ja.ipynb](AutoModel/Alpaca_LoRA_ja.ipynb) | Finetuning and deploying Alpaca-LoRA with translated Alpaca Dataset |
| [Alpaca_Inference_ja.ipynb](AutoModel/Alpaca_Inference_ja.ipynb) | Finetuning Alpaca-LoRA with Alpaca Dataset |
| [Cerebras_Finetune.ipynb](AutoModel/Cerebras_Finetune.ipynb) | Finetuning and deploying Cerebras with Dolly Dataset |
| [Cerebras_Inference.ipynb](AutoModel/Cerebras_Inference.ipynb) | Deploy pre-trained Cerebras |
| [Cerebras_LoRA.ipynb](AutoModel/Cerebras_LoRA.ipynb) | Finetuning and deploying Cerebras using LoRA with Dolly Dataset |
| [Cerebras_LoRA_ja.ipynb](AutoModel/Cerebras_LoRA_ja.ipynb) | Finetuning and deploying Cerebras using LoRA with translated Dolly Dataset |
| [StableLM_Inference.ipynb](AutoModel/StableLM_Inference.ipynb) | Deploy pre-trained StableLM |
| [StableLM_LoRA.ipynb](AutoModel/StableLM_LoRA.ipynb) | Finetuning and deploying StableLM using LoRA with Dolly Dataset |
| [Dolly_v2_Inference.ipynb](AutoModel/Dolly_v2_Inference.ipynb) | Deploy pre-trained Dolly v2 |
| [Dolly_v2_LoRA.ipynb](AutoModel/Dolly_v2_LoRA.ipynb) | Finetuning and deploying Dolly v2 using LoRA with Dolly Dataset |
| [OpenCALM_Inference_ja.ipynb](AutoModel/OpenCALM_Inference_ja.ipynb) | Deploy OpenCALM |
| [OpenCALM_LoRA_ja.ipynb](AutoModel/OpenCALM_LoRA_ja.ipynb) | Finetuning and deploying CALM using LoRA with Dolly Dataset |
| [Rinna_Neox_Inference_ja.ipynb](AutoModel/Rinna_Neox_Inference_ja.ipynb) | Deploy Rinna NeoX |
| [Rinna_Neox_LoRA_ja.ipynb](AutoModel/Rinna_Neox_LoRA_ja.ipynb) | Finetuning and deploying Rinna NeoX with Dolly Dataset|
| [MPT_Inference.ipynb](AutoModel/MPT_Inference.ipynb) | Deploy pre-trained MPT |
| [MPT_LoRA.ipynb](AutoModel/MPT_LoRA.ipynb) | Finetuning and deploying MPT using LoRA with Dolly Dataset |
| [MPT_LoRA_ja.ipynb](AutoModel/MPT_LoRA_ja.ipynb) | Finetuning and deploying MPT using LoRA with |
| [RWKV_Inference.ipynb](AutoModel/RWKV_Inference.ipynb) | Deploying Pre-trained RWKV |
| [RWKV_Finetune.ipynb](RWKV/RWKV_Finetune.ipynb) | Finetuning and deploying RWKV with Dolly Dataset |
| [RWKV_LoRA.ipynb](RWKV/RWKV_Finetune.ipynb) | Finetuning and deploying RWKV using LoRA with Dolly Dataset |
| [RWKV_LoRA_ja.ipynb](RWKV/RWKV_Finetune.ipynb) | Finetuning and deploying RWKV using LoRA with translated Dolly Dataset |
| [RWKV_Inference.ipynb](RWKV/RWKV_Inference.ipynb) | Deploying Pre-trained RWKV |
| [RWKV_Inference_ja.ipynb](RWKV/RWKV_Inference_ja.ipynb) | Deploying Pre-trained RWKV supporting Japanese |
