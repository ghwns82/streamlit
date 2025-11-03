import streamlit as st
from PIL import Image
import io

st.title("📷 카메라로 얼굴 등록하기")

# 카메라 입력
img_file = st.camera_input("얼굴을 촬영하세요")

if img_file is not None:
    # 촬영된 이미지를 바로 보여주기
    st.image(img_file)

    # PIL 이미지로 변환해서 처리하기 (예: 서버 업로드, 얼굴 인식 등)
    img = Image.open(img_file)
    st.write("이미지 크기:", img.size)
