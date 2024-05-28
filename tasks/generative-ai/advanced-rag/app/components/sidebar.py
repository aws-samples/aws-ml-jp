import streamlit as st

def sidebar():
    st.sidebar.header("Settings")
    aws_region = st.sidebar.selectbox("AWS Region", ("us-west-2", "us-east-1"))
    # Amazon Kendra の設定
    st.sidebar.subheader("Amazon Kendra")
    kendra_index_id = st.sidebar.text_input("Kendra Index ID", key="kendra_index_id")
    # Amazon Bedrock の設定
    st.sidebar.subheader("Amazon Bedrock")
    generator_model_id = st.sidebar.selectbox(
        "Generator Model ID",
        (
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0",
        )
    )
    # RAG の設定
    st.sidebar.subheader("RAG")
    run_rag = st.sidebar.checkbox("RAG の結果を表示")
    #use_advanced_rag = st.sidebar.checkbox("Use Advanced RAG")
    # 検索前処理
    preretrieval_method = st.sidebar.radio("Pre-retrieval method", ("なし", "クエリ拡張"))
    # 検索後処理
    postretrieval_method = st.sidebar.radio("Post-retrieval method", ("なし", "検索結果の関連度評価"))
    return {
        #"use_advanced_rag": use_advanced_rag,
        "run_rag": run_rag,
        "kendra_index_id": kendra_index_id,
        "aws_region": aws_region,
        "generator_model_id": generator_model_id,
        "preretrieval_method": preretrieval_method,
        "postretrieval_method": postretrieval_method,
    }
