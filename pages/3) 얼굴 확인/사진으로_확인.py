import streamlit as st
import requests

from config import BACK_URL

st.title("🖼️ 사진으로 얼굴 확인하기")
st.caption("이미지 한 장을 업로드하면 FastAPI로 보내서 누구인지 확인합니다.")

API_URL =BACK_URL+'/predict'

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
                    if "student_id" in data:
                        name = data.get("student_id")
                        conf = data.get("score")
                    else:
                        candidates = None
                else:
                    candidates = None

                if name:
                    st.success(f"식별 결과: **{name}**"
                               + (f"  (confidence: {conf:.3f})" if isinstance(conf, (int, float)) else ""))
                # elif candidates:
                #     st.subheader("후보 결과")
                #     # 상위 5개만 표시
                #     rows = []
                #     for c in candidates[:5]:
                #         rows.append({
                #             "name": c.get("name") or c.get("identity") or "unknown",
                #             "confidence": c.get("confidence") or c.get("score"),
                #         })
                #     st.dataframe(rows, use_container_width=True)
                else:
                    st.warning("응답을 해석할 수 없습니다. 서버 응답 스키마를 확인하세요.")
        except requests.exceptions.RequestException as e:
            st.error(f"네트워크 오류: {e}")
