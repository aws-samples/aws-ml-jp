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
| [Alpaca_LoRA.ipynb](Transformers/Alpaca_LoRA.ipynb) | Finetuning and deploying Alpaca-LoRA with Alpaca Dataset |
| [Alpaca_Inference.ipynb](Transformers/Alpaca_Inference.ipynb) | Deploy pre-trained Alpaca-LoRA |
| [Alpaca_LoRA_ja.ipynb](Transformers/Alpaca_LoRA_ja.ipynb) | Finetuning and deploying Alpaca-LoRA with translated Alpaca Dataset |
| [Alpaca_Inference_ja.ipynb](Transformers/Alpaca_Inference_ja.ipynb) | Finetuning Alpaca-LoRA with Alpaca Dataset |
| [Cerebras_Finetune.ipynb](Transformers/Cerebras_Finetune.ipynb) | Finetuning and deploying Cerebras with Dolly Dataset |
| [Cerebras_Inference.ipynb](Transformers/Cerebras_Inference.ipynb) | Deploy pre-trained Cerebras |
| [Cerebras_LoRA.ipynb](Transformers/Cerebras_LoRA.ipynb) | Finetuning and deploying Cerebras using LoRA with Dolly Dataset |
| [Cerebras_LoRA_ja.ipynb](Transformers/Cerebras_LoRA_ja.ipynb) | Finetuning and deploying Cerebras using LoRA with translated Dolly Dataset |
| [StableLM_Inference.ipynb](Transformers/StableLM_Inference.ipynb) | Deploy pre-trained StableLM |
| [StableLM_LoRA.ipynb](Transformers/StableLM_LoRA.ipynb) | Finetuning and deploying StableLM using LoRA with Dolly Dataset |
| [Dolly_v2_Inference.ipynb](Transformers/Dolly_v2_Inference.ipynb) | Deploy pre-trained Dolly v2 |
| [Dolly_v2_LoRA.ipynb](Transformers/Dolly_v2_LoRA.ipynb) | Finetuning and deploying Dolly v2 using LoRA with Dolly Dataset |
| [OpenCALM_Inference_ja.ipynb](Transformers/OpenCALM_Inference_ja.ipynb) | Deploy OpenCALM |
| [OpenCALM_Inference_jaqket.ipynb](Transformers/OpenCALM_Inference_jaqket.ipynb) | Deploy OpenCALM and inference for [JAQKET](https://www.nlp.ecei.tohoku.ac.jp/projects/jaqket/) dataset |
| [OpenCALM_LoRA_ja.ipynb](Transformers/OpenCALM_LoRA_ja.ipynb) | Finetuning and deploying OpenCALM using LoRA with Dolly Dataset |
| [OpenCALM_LoRA_jaqket.ipynb](Transformers/OpenCALM_LoRA_jaqket.ipynb) | Finetuning and deploying OpenCALM using LoRA with [JAQKET](https://www.nlp.ecei.tohoku.ac.jp/projects/jaqket/) dataset |
| [Rinna_Neox_Inference_ja.ipynb](Transformers/Rinna_Neox_Inference_ja.ipynb) | Deploy Rinna NeoX |
| [Rinna_Neox_LoRA_ja.ipynb](Transformers/Rinna_Neox_LoRA_ja.ipynb) | Finetuning and deploying Rinna NeoX with Dolly Dataset|
| [MPT_Inference.ipynb](Transformers/MPT_Inference.ipynb) | Deploy pre-trained MPT |
| [MPT_LoRA.ipynb](Transformers/MPT_LoRA.ipynb) | Finetuning and deploying MPT using LoRA with Dolly Dataset |
| [MPT_LoRA_ja.ipynb](Transformers/MPT_LoRA_ja.ipynb) | Finetuning and deploying MPT using LoRA with |
| [RWKV_Inference.ipynb](Transformers/RWKV_Inference.ipynb) | Deploying Pre-trained RWKV |
| [RWKV_Finetune.ipynb](RWKV/RWKV_Finetune.ipynb) | Finetuning and deploying RWKV with Dolly Dataset |
| [RWKV_LoRA.ipynb](RWKV/RWKV_Finetune.ipynb) | Finetuning and deploying RWKV using LoRA with Dolly Dataset |
| [RWKV_LoRA_ja.ipynb](RWKV/RWKV_Finetune.ipynb) | Finetuning and deploying RWKV using LoRA with translated Dolly Dataset |
| [RWKV_Inference.ipynb](RWKV/RWKV_Inference.ipynb) | Deploying Pre-trained RWKV |
| [RWKV_Inference_ja.ipynb](RWKV/RWKV_Inference_ja.ipynb) | Deploying Pre-trained RWKV supporting Japanese |
