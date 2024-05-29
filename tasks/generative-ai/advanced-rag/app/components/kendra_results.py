import streamlit as st
from utils.kendra_api import search_kendra
from utils.s3_utils import generate_presigned_url


def kendra_results(query, settings):
    kendra_response = search_kendra(query, settings)

    st.write(f"{len(kendra_response)} 件の検索結果")
    
    for result in kendra_response:
        document_title = result["DocumentTitle"]["Text"]
        document_id = result["DocumentId"]
        document_excerpt = result["DocumentExcerpt"]["Text"]
        highlights = result["DocumentExcerpt"]["Highlights"]
            
        # ハイライトされた箇所を太字にする
        highlighted_excerpt = []
        previous_end = 0
        for i, highlight in enumerate(highlights):
            start = highlight["BeginOffset"]
            end = highlight["EndOffset"]
            highlighted_excerpt.append(f"{document_excerpt[previous_end:start]} **{document_excerpt[start:end]}** ")
            previous_end = end
        highlighted_excerpt = "".join(highlighted_excerpt)
        
        st.markdown(f"##### {document_title}")
        if document_id.startswith("s3://"):
                # S3 URIの場合、presigned URLを発行してリンクを表示
                s3_uri_parts = document_id[5:].split("/", 1)
                bucket_name = s3_uri_parts[0]
                object_name = s3_uri_parts[1]
                presigned_url = generate_presigned_url(bucket_name, object_name)
                if presigned_url:
                    st.markdown(f"{document_id} [\[View Document\]]({presigned_url})")
                else:
                    st.write("Failed to generate presigned URL.")
        else:
            st.write(f"Document ID: {document_id}")
        st.caption(highlighted_excerpt.replace("\n", ""))
