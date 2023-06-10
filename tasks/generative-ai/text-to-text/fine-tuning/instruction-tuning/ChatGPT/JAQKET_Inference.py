import os
import json
import requests
import pandas as pd
import openai


OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
JAQKET_DEV_DATASET = "https://jaqket.s3.ap-northeast-1.amazonaws.com/data/aio_02/aio_02_dev_v1.0.jsonl"


if OPENAI_ORGANIZATION is None or OPENAI_API_KEY is None:
    raise Exception("Please set the OPENAI_ORGANIZATION and OPENAI_API_KEY environment variables for organization and api key.")


def answer(question: str) -> str:
    openai.organization = OPENAI_ORGANIZATION
    openai.api_key = OPENAI_API_KEY

    template = """質問:{}\n回答:"""
    
    response = openai.Completion.create(
      model="text-davinci-003",
      prompt=template.format(question),
      max_tokens=64,
      temperature=0,
      top_p=1,
      n=1,
      stop="\n"
    )
    
    answer = response["choices"][0]["text"]
    return answer


def read_jaqket_dev() -> pd.DataFrame:
    file_name = os.path.basename(JAQKET_DEV_DATASET)
    location = os.path.join(os.path.dirname(__file__), f"data/{file_name}")
    if not os.path.exists(location):
        response = requests.get(JAQKET_DEV_DATASET)
        with open(location, mode="wb") as f:
            f.write(response.content)
    
    return pd.read_json(location, lines=True)


def answer_jaqket(question_df: pd.DataFrame, limit=3) -> pd.DataFrame:
    target_df = question_df
    if limit > 0:
        target_df = question_df.head(limit)
    
    target_df["chatgpt_answer"] = target_df.question.map(answer)
    
    def match(row) -> bool:
        answers = row["answers"]
        chatgpt_answer = row["chatgpt_answer"]
        if chatgpt_answer in answers:
            return True
        else:
            return False
    
    target_df["matched"] = target_df.apply(match, axis=1)
    return target_df


if __name__ == "__main__":
    answer_file_name = "jaqket_answers.csv"
    location = os.path.join(os.path.dirname(__file__), f"data/{answer_file_name}")
    answers = answer_jaqket(read_jaqket_dev())
    answers.to_csv(location, index=False)
