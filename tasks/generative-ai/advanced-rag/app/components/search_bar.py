import streamlit as st

def search_bar():
    query = st.text_input("Enter your question:", key="search_bar")
    return query
