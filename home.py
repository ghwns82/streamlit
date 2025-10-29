import streamlit as st

st.set_page_config(page_title="메인 페이지", page_icon="🏠")

st.title("메인 페이지")
st.write("아래에서 원하는 기능을 선택하세요 👇")

# 페이지 링크 버튼
col1, col2,col3 = st.columns(3)

with col1:
    if st.button("📘 얼굴 등록"):
        st.switch_page("pages/page1.py")

with col2:
    if st.button("📗 얼굴 검사"):
        st.switch_page("pages/page2.py")


with col3:
    if st.button("📗 얼굴 검사2"):
        st.switch_page("pages/page3.py")
