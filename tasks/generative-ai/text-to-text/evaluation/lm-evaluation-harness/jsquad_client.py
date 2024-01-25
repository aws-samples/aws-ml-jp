import json
import time
import io
from typing import Optional, Union
from datetime import datetime

import boto3
from lm_eval.tasks.ja.jsquad import JSQuAD


class JSQuADClient(JSQuAD):
    def __init__(self, region_name: Optional[str] = None) -> None:
        # Access to Amazon Bedrock
        # Please speficy region_name that model access is allowed, or preset it by aws configure.
        super().__init__()
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.batch_client = boto3.client("bedrock", region_name=region_name)
        self.s3 = boto3.resource("s3", region_name=region_name)
        self.identity = boto3.client("sts").get_caller_identity()

    def ask(
        self,
        prompt: str,
        model_id: str,
        max_length: int = 1024,
        temperature: float = 1.0,
        top_p: float = 0.99,
    ) -> str:
        raise NotImplementedError

    def ask_batch(
        self,
        prompts: list[str],
        model_id: str,
        max_length: int = 1024,
        temperature: float = 1.0,
        top_p: float = 0.99,
    ) -> list[str]:
        raise NotImplementedError

    def _send_prompt(
        self,
        model_id: str,
        body: dict,
        accept: str = "application/json",
        content_type: str = "application/json",
    ) -> dict:
        response = self.client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            accept=accept,
            contentType=content_type,
        )

        return response

    def compute(
        self, docs: Union[dict, list[dict]], answers: Union[str, list[str]]
    ) -> dict:
        _docs = docs
        if not isinstance(docs, list):
            _docs = [docs]

        references = [
            {
                "id": d["question_id"],
                "answers": [{"text": d["output"], "answer_start": d["output_start"]}],
            }
            for d in _docs
        ]

        _answers = answers
        if not isinstance(answers, list):
            _answers = [answers]

        predictions = [
            {
                "id": d["question_id"],
                "prediction_text": a,
            }
            for d, a in zip(_docs, _answers)
        ]

        return self.jasquad_metric.compute(
            predictions=predictions, references=references
        )


class JSQuADClaude(JSQuADClient):
    """
    Reference:
    - Anthropic Claude Prompt Guide: https://docs.anthropic.com/claude/docs/introduction-to-prompt-design
    """

    PROMPT_VERSION = 9.9  # Avoid the conflict of existing version
    SEP = "\n"

    def doc_to_text(self, doc: dict, samples: list[dict] = ()) -> str:
        context = doc["input"].split("[SEP]")[-1].strip()
        question = doc["instruction"]
        task_context = f"与えられたinputからinstructionに対する回答を抽出する関数を実行してください。"
        examples = ""
        if len(samples) > 0:
            examples = "\n\n入出力のexampleを示します。\n\n"
            for sample in samples:
                sample_input = sample["input"].split("[SEP]")[-1].strip()
                sample_instruction = sample["instruction"]
                sample_answer = sample["output"]

                sample_input = f"<input>{sample_input}</input>"
                sample_instruction = f"<instruction>{sample_instruction}</instruction>"
                examples += f"<example>\n{sample_input}\n{sample_instruction}\nAnswer:{sample_answer}\n</example>\n"

        input_text = "\n".join([
            task_context,
            examples,
            "次のinputからinstructionに対する回答を抽出してください。結果はAnswer:の後に記載し名詞以外何も含まないことを厳守してください。",
            f"<input>{context}</input>",
            f"<instruction>{question}</instruction>"
        ])
        return f"\n\nHuman: {input_text}\n\nAssistant:Answer:"

    def choose_model(self, version, instant=False):
        if instant:
            # instant is only v1
            model_id = "anthropic.claude-instant-v1"
        else:
            if version == "1":
                model_id = "anthropic.claude-v1"
            elif version == "2":
                model_id = "anthropic.claude-v2"
            elif version == "2.1":
                model_id = "anthropic.claude-v2:1"
            else:
                model_id = "anthropic.claude-v2"

        return model_id

    def ask(
        self,
        prompt: str,
        model_id: str,
        max_length: int = 1024,
        temperature: float = 1.0,
        top_p: float = 0.99,
    ) -> str:
        body = {
            "prompt": prompt,
            "max_tokens_to_sample": max_length,
            "temperature": temperature,
            "top_p": top_p,
        }
        response = self._send_prompt(model_id, body)
        response_body = json.loads(response.get("body").read())  # type: ignore
        reply = response_body.get("completion")
        return reply

    def ask_batch(
        self,
        bucket_name: str,
        prompts: list[str],
        model_id: str,
        max_length: int = 1024,
        temperature: float = 1.0,
        top_p: float = 0.99,
        role_arn: str = "",
    ) -> list[str]:
        requests = []
        # Upload file format
        # https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference-data.html
        for i, prompt in enumerate(prompts):
            body = {
                "prompt": prompt,
                "max_tokens_to_sample": max_length,
                "temperature": temperature,
                "top_p": top_p,
            }
            record = {"recordId": str(i).zfill(12), "modelInput": body}
            requests.append(json.dumps(record))

        jsonl_data = "\n".join(requests)

        # upload to S3
        now = datetime.now()
        job_name = f"{type(self).__name__}-{now.strftime('%Y%m%d-%H%M%S')}"
        input_key = f"input/{job_name}.jsonl"
        self.s3.Object(bucket_name, input_key).put(Body=jsonl_data)

        # Create batch inference job
        inputDataConfig = {
            "s3InputDataConfig": {"s3Uri": f"s3://{bucket_name}/{input_key}"}
        }

        outputDataConfig = {
            "s3OutputDataConfig": {"s3Uri": f"s3://{bucket_name}/output/{job_name}/"}
        }

        _role_arn = role_arn if role_arn else self.identity["Arn"]
        # Todo: fix patch code
        _role_arn = (
            _role_arn.replace(":sts:", ":iam:")
            .replace("assumed-role/", "role/service-role/")
            .replace("/SageMaker", "")
        )
        print(_role_arn)
        response = self.batch_client.create_model_invocation_job(
            roleArn=_role_arn,
            modelId=model_id,
            jobName=job_name,
            inputDataConfig=inputDataConfig,
            outputDataConfig=outputDataConfig,
        )

        job_id = response.get("jobArn")
        status = self.batch_client.get_model_invocation_job(jobIdentifier=job_id)[
            "status"
        ]
        # kinds of status
        # https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference-list.html
        while status not in ("Completed", "Failed", "Stopped"):
            time.sleep(5)
            status = self.batch_client.get_model_invocation_job(jobIdentifier=job_id)[
                "status"
            ]

        contents = []
        if status == "Completed":
            # Output file format
            # https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference-create.html
            bucket = self.s3.Bucket(bucket_name)
            job_id_base = job_id.split("/")[-1].strip()
            for _object in bucket.objects.filter(
                Prefix=f"output/{job_name}/{job_id_base}"
            ):
                if _object.key.endswith(".jsonl.out"):
                    _file = bucket.Object(_object.key).get()
                    _contents = _file["Body"].read()
                    for line in io.BytesIO(_contents):
                        contents.append(json.loads(line.decode("utf-8")))
        else:
            raise Exception(f"Batch inference {job_id} finished status {status}.")

        answers = []
        contents = sorted(contents, key=lambda x: x["recordId"])
        for content in contents:
            answer = content["modelOutput"].get("completion")
            answers.append(answer)

        return answers
