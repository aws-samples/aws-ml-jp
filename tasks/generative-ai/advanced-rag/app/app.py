import streamlit as st
from components.search_bar import search_bar
from components.rag_result import rag_result
from components.kendra_results import kendra_results
from components.sidebar import sidebar
from components.tutorial import tutorial

def main():
    st.set_page_config(page_title="Advanced RAG Demo", layout="wide")
    st.title("Advanced RAG Demo")

    # サイドバーの設定
    settings = sidebar()
    
    # RAGを実行するかどうかのチェックボックス
    run_rag = settings["run_rag"]
    kendra_index_id = settings["kendra_index_id"]

    # 検索バーの表示
    query = search_bar()

    if query:
        # RAG結果用のプレースホルダーを作成
        rag_placeholder = st.container(border=True)

        # Amazon Kendraによる検索結果の表示
        kendra_results(query, kendra_index_id)
        #kendra_response = kendra_results(query)
        #st.markdown("### Kendra Search Results")
        #st.write(kendra_response)

        if run_rag:
            # RAGの回答生成
            rag_placeholder.markdown("#### RAG Answer 🤖")
            with rag_placeholder:
                rag_result(query, settings)
                #for chunk in rag_result(query, settings):
                #    st.write(chunk)
        
    # チュートリアルの表示
    tutorial()

if __name__ == "__main__":
    main()