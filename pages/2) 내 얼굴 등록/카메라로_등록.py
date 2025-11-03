import streamlit as st
import requests
import os

from config import BACK_URL

st.title("📷 카메라로 얼굴 등록하기")

# 카메라 입력
img_file = st.camera_input("얼굴을 촬영하세요")


st.set_page_config(page_title="업로드", page_icon="📤")
st.title("텍스트 + 이미지 → FastAPI /regist")

API_URL =BACK_URL+'/regist'


with st.form("upload_form"):
    student_name = st.text_input("이름 (필수, 영문)")
    student_id = st.text_input("교번 (필수)")
    image = img_file
    submitted = st.form_submit_button("전송")

if submitted:
    if not student_name:
        st.error("이름 필수입니다.")
    elif not student_id:
        st.error("학번(교번)은 필수입니다.")
    elif not image:
        st.error("file(이미지)를 업로드하세요.")
    else:
        try:
            # 파일 파트: 키 이름은 반드시 'file'
            files = {
                "file": (image.name, image.getvalue(), image.type or "application/octet-stream")
            }
            # 폼 데이터: 
            data = {"student_name": student_name,'student_id':student_id}

            with st.spinner("전송 중..."):
                resp = requests.post(API_URL, data=data, files=files, timeout=60)

            if resp.ok:
                st.success("성공 🎉")
                st.json(resp.json())
                st.image(image, caption="업로드 미리보기")
            else:
                st.error(f"실패: {resp.status_code}\n{resp.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"네트워크 오류: {e}")