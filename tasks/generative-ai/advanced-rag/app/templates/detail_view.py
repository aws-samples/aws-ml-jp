import streamlit as st

def detail_view(item):
    st.markdown("### Detail View")
    st.write("Title:", item["Title"])
    st.write("Content:", item["Content"])
    st.write("Score:", item["Score"])
