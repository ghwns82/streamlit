import streamlit as st
import requests
import os
import cv2
import numpy as np
from PIL import Image
from config import BACK_URL
import matplotlib.pyplot as plt

st.title("🖼️ 사진으로 얼굴 확인하기")
st.caption("이미지 한 장을 업로드하면 FastAPI로 보내서 누구인지 확인합니다.")
API_URL =BACK_URL+'/predict_many'

show_raw = st.checkbox("서버 원본 응답(JSON)도 표시", value=False)

image = st.file_uploader("이미지 업로드", type=["jpg", "jpeg", "png", "webp"])

if image:
    st.image(image, caption="업로드 미리보기")

if st.button("식별 요청 보내기"):
    if not image:
        st.error("이미지를 업로드하세요.")
    else:
        try:
            files = {"file": (image.name, image.getvalue(), image.type or "application/octet-stream")}
            with st.spinner("식별 중..."):
                resp = requests.post(API_URL, files=files, timeout=60)
            if not resp.ok:
                st.error(f"요청 실패: {resp.status_code}\n{resp.text}")
            else:
                data = resp.json()
                if show_raw:
                    st.subheader("Raw Response")
                    st.json(data)

                name = None
                conf = None
                candidates = None

                if isinstance(data, dict):
                    known, unknown = data.get("known"), data.get("unknown")
                    st.success(f"식별 결과: Recognized: {known} Unrecognized: {unknown}")

                    pil_img = Image.open(image)
                    img = np.array(pil_img)
                    y = []
                    x = []
                    for i,dic in enumerate(data.get('detail')):
                        xmin, ymin,xmax, ymax = dic.get('points')
                        if 'unknown' == dic.get('student_name'):
                            cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (255,0,0), 2)
                            x.append(i)
                        else:
                            cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (0,255,0), 2)
                            x.append(dic.get('student_name'))
                        y.append(dic.get('score'))
                    st.image(img)
                    y2 = [ ['gray','red'][i>0.4] for i in y]
                    # fig,ax= plt.subplots()
                    fig,ax= plt.subplots(figsize=(6, 10))
                    ax.barh(range(len(y)),y,color=y2)
                    ax.set_yticks(range(len(y)))
                    ax.set_yticklabels(x)
                    ax.axvline(0.4, color='red', linestyle='--', linewidth=1)
                    st.pyplot(fig)


                    
                else:
                    st.warning("응답을 해석할 수 없습니다. 서버 응답 스키마를 확인하세요.")
        except requests.exceptions.RequestException as e:
            st.error(f"네트워크 오류: {e}")
