import streamlit as st

def comparison_view(rag_result, advanced_rag_result):
    st.markdown("### Comparison View")
    st.write("#### RAG Result")
    st.write(rag_result)
    st.write("#### Advanced RAG Result")
    st.write(advanced_rag_result)
