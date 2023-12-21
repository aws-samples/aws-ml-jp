import subprocess
from time import sleep
# import sagemaker_ssh_helper
# sagemaker_ssh_helper.setup_and_start_ssh()

import os

import os, argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--model", type=str, default="rinna/japanese-gpt-neox-3.6b-instruction-ppo"
)
parser.add_argument("--peft", type=str)
parser.add_argument("--task", type=str, default="jsquad-1.1-0.4")
parser.add_argument("--num_fewshot", type=int, default=2)
args = parser.parse_args()


subprocess.run("chmod -R 777 /opt/ml/", shell=True)

peft = ",peft=/opt/ml/input/data/train" if args.peft else ""

model_args = f"pretrained={args.model}{peft},use_fast=False"

start_cmd = f"python main.py --model hf-causal-experimental --model_args {model_args} --tasks '{args.task}' --num_fewshot '{int(args.num_fewshot)}' --device 'cuda' --output_path '/opt/ml/model/result.json'"

subprocess.run(start_cmd, shell=True)
