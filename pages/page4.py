import streamlit as st
import requests
import os

st.set_page_config(page_title="업로드", page_icon="📤")
st.title("텍스트 + 이미지 → FastAPI /regist")

API_URL ="http://220.149.231.136:9404"+'/regist'


with st.form("upload_form"):
    text = st.text_input("이름 (필수)")
    text2 = st.text_input("교번 (필수)")
    submitted = st.form_submit_button("전송")

if submitted:
    if not text:
        st.error("text는 필수입니다.")
    elif not text2:
        st.error("text는 필수입니다.")
    else:
        try:          
            # 폼 데이터: 키 이름은 반드시 'text'
            data = {"text": text,'text2':text2}

            with st.spinner("전송 중..."):
                resp = requests.post(API_URL, data=data, files=files, timeout=60)

            if resp.ok:
                st.success("성공 🎉")
                st.json(resp.json())
            else:
                st.error(f"실패: {resp.status_code}\n{resp.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"네트워크 오류: {e}")
