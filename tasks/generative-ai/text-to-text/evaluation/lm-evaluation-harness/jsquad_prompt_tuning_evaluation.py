import json
from typing import Optional, Union

import boto3
from lm_eval.tasks.ja.jsquad import JSQuAD

# read JSQuAD

# creat prompt

# inference by Amazon Bedrock

# evaluate the answer


class JSQuADClaude(JSQuAD):
    """
    Reference:
    - Anthropic Claude Prompt Guide: https://docs.anthropic.com/claude/docs/introduction-to-prompt-design
    """

    PROMPT_VERSION = 9.9  # Avoid the conflict of existing version
    SEP = "\n"

    def doc_to_text(self, doc: dict) -> str:
        context = doc["input"].split("[SEP]")[-1].strip()
        question = doc["instruction"]
        input_text = f"inputを注意深く読み、instructionに対する回答となる名詞を正確に抽出してください。"\
            "回答の名詞以外に何も含まないことを厳守してください。\n"\
            f"<input>{context}</input>\n"\
            f"<instruction>{question}</instruction>"
        return f"\n\nHuman: {input_text}\n\nAssistant:"

    def compute(self, docs: Union[dict, list[dict]], answers: Union[str, list[str]]) -> dict:
        _docs = docs
        if not isinstance(docs, list):
            _docs = [docs]

        references = [{
            "id": d["question_id"],
            "answers": [
                {
                  "text": d["output"],
                  "answer_start": d["output_start"]
                }
              ]
        } for d in _docs]

        _answers = answers
        if not isinstance(answers, list):
            _answers = [answers]
        
        predictions = [{
            "id": d["question_id"],
            "prediction_text": a,
        } for d, a in zip(_docs, _answers)]
        
        return self.jasquad_metric.compute(
            predictions=predictions, references=references
        )

class Bedrock:
    def __init__(self, region_name: Optional[str] = None) -> None:
        # Access to Amazon Bedrock
        # Please speficy region_name that model access is allowed, or preset it by aws configure.
        self.client = boto3.client("bedrock-runtime", region_name=region_name)

    def ask_to_claude(
        self,
        prompt: str,
        version: str = "2",
        instant: bool = True,
        max_length: int = 1024,
        temperature: float = 1.0,
        top_p: float = 0.99,
    ) -> str:
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
