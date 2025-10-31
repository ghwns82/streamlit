import streamlit as st
import requests
import os

st.set_page_config(page_title="업로드", page_icon="📤")
st.title("텍스트 + 이미지 → FastAPI /regist")

API_URL = API_KEY = os.getenv("API_URL")+'/regist'


with st.form("upload_form"):
    text = st.text_input("이름 (필수)")
    text2 = st.text_input("교번 (필수)")
    image = st.file_uploader("file (이미지)", type=["png", "jpg", "jpeg", "webp"])
    submitted = st.form_submit_button("전송")

if submitted:
    if not text:
        st.error("text는 필수입니다.")
    elif not text2:
        st.error("text는 필수입니다.")
    elif not image:
        st.error("file(이미지)를 업로드하세요.")
    else:
        try:
            # 파일 파트: 키 이름은 반드시 'file'
            files = {
                "file": (image.name, image.getvalue(), image.type or "application/octet-stream")
            }
            # 폼 데이터: 키 이름은 반드시 'text'
            data = {"text": text,'text2':text2}

            with st.spinner("전송 중..."):
                resp = requests.post(API_URL, data=data, files=files, timeout=60)

            if resp.ok:
                st.success("성공 🎉")
                st.json(resp.json())
                st.image(image, caption="업로드 미리보기", use_column_width=True)
            else:
                st.error(f"실패: {resp.status_code}\n{resp.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"네트워크 오류: {e}")
