import re
import streamlit as st
from utils.rag_api import generate_rag_answer
from utils.s3_utils import generate_presigned_url_from_s3_uri

def rag_result(query, settings):
    # RAGの回答をチャンクで生成するジェネレータを呼び出す
    #for chunk in generate_rag_answer(query, settings):
    #    yield chunk
    final_state = generate_rag_answer(query, settings)
    #st.markdown(final_state["keys"]["generation"])

    xml = final_state["keys"]["generation"]
    st.markdown(parse_answer(xml))


def parse_answer(xml):
    answer_parts = re.findall(r'<answer_part>(.*?)</answer_part>', xml, re.DOTALL)
    result = ""
    source_refs = ""
    source_index = 1
    unique_refs = set()
    source_dic = {}
    for part in answer_parts:
        text = re.search(r'<text>(.*?)</text>', part, re.DOTALL).group(1).strip()
        sources = re.findall(r'<source>(.*?)</source>', part, re.DOTALL)
        source_str = ""
        for source in sources:
            document_id = re.search(r'<document_id>(.*?)</document_id>', source).group(1)
            title = re.search(r'<title>(.*?)</title>', source).group(1)
            if title in unique_refs:
                source_str += f" \[{source_dic[title]}\]"
            else:
                source_str += f" \[{source_index}\]"
                unique_refs.add(title)
                source_dic[title] = source_index
                if document_id.startswith("s3://"):
                    presigned_url = generate_presigned_url_from_s3_uri(document_id)
                    source_refs += f"\[{source_index}\] [{title}]({presigned_url})  \n"
                else:
                    source_refs += f"\[{source_index}\] {title}  \n"
                source_index += 1
        result += f"{text}{source_str}\n\n"
    return result + "\n\n" + source_refs
