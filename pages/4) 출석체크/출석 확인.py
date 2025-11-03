import streamlit as st
import requests
import os
from config import BACK_URL

st.set_page_config(page_title="출석체크", page_icon="📤")
st.title("🕒 출석체크확인")

API_URL =BACK_URL+'/attendance'


with st.form("upload_form"):
    name = st.text_input("이름 (필수,영문)")
    ID = st.text_input("학번 (필수)")
    submitted = st.form_submit_button("전송")

if submitted:
    if not ID:
        st.error("학번은 필수입니다.")
    else:
        try:          
            # 폼 데이터: 키 이름은 반드시 'text'
            data = {"ID": ID}

            with st.spinner("전송 중..."):
                resp = requests.post(API_URL, data=data, timeout=60)

            if resp.ok:
                st.success("성공 🎉")
                st.json(resp.json())
            else:
                st.error(f"실패: {resp.status_code}\n{resp.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"네트워크 오류: {e}")
