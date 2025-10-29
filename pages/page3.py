# app_webrtc_every2s.py
import time
import threading
from typing import Any, Dict, Optional

import cv2
import av
import requests
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase

st.set_page_config(page_title="실시간 얼굴 식별 (2초 주기)", page_icon="🧑‍💼")
st.title("🧑‍💼 실시간 얼굴 식별")
st.caption("실시간 카메라를 표시하고, 정확히 2초마다 FastAPI로 프레임을 전송합니다.")

# 네가 쓰던 스타일에 맞춰 상수로 둠
RECOGNITION_API = st.text_input(
    "FastAPI 엔드포인트",
    value="https://fastapi-3uqk.onrender.com/predict",
    help="POST multipart/form-data 로 file=이미지 전송",
)
show_raw = st.checkbox("서버 원본 응답(JSON) 표시", value=False)

# 최신 응답 패널(계속 유지)
result_box = st.empty()
raw_box = st.empty()

def _safe_parse_label(data: Any) -> str:
    """
    네가 준 로직을 존중:
    - data.get('predictions', {})에서 'ResNet18' 키를 우선 사용
    - 없으면 name/id/identity 등을 순서대로 시도
    - 전혀 없으면 'Unknown'
    """
    try:
        if isinstance(data, dict):
            preds = data.get("predictions", {})
            if isinstance(preds, dict):
                label = preds.get("ResNet18")
                if label:
                    return str(label)

            # 단일 결과 타입 대응
            for k in ("name", "id", "identity", "label"):
                if k in data and data[k]:
                    return str(data[k])

            # 리스트 형태 predictions 대응
            if isinstance(preds, list) and preds:
                cand = preds[0]
                if isinstance(cand, dict):
                    for k in ("name", "identity", "id", "label"):
                        if k in cand and cand[k]:
                            return str(cand[k])
        return "Unknown"
    except Exception:
        return "Unknown"

class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame_count = 0
        self.result_label = "..."
        self.request_interval = 2.0   # ✅ 정확히 2초 간격(초)
        self.last_sent_ts = 0.0
        self.lock = threading.Lock()
        self.last_json: Optional[Dict] = None

    def send_frame_to_backend(self, img):
        try:
            ok, img_encoded = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if not ok:
                label = "Error"
            else:
                response = requests.post(
                    RECOGNITION_API,
                    files={"file": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")},
                    timeout=10,  # ✅ 넉넉한 타임아웃
                )
                if response.status_code == 200:
                    data = response.json()
                    label = _safe_parse_label(data)
                else:
                    data = {"error": f"HTTP {response.status_code}", "text": response.text}
                    label = "Error"
        except Exception as e:
            # 콘솔에 에러 메시지 출력(네가 하던 것 유지)
            print("🔥 예외 발생:", e)
            data = {"error": "network", "message": str(e)}
            label = "Error"

        # 결과 업데이트
        with self.lock:
            self.result_label = label
            self.last_json = data

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1

        # ✅ 프레임 카운트 대신 '시간' 기준 스로틀링 (정확히 2초마다)
        now = time.time()
        if now - self.last_sent_ts >= self.request_interval and RECOGNITION_API:
            self.last_sent_ts = now
            threading.Thread(target=self.send_frame_to_backend, args=(img.copy(),), daemon=True).start()

        # 현재 라벨을 프레임에 오버레이
        with self.lock:
            label_to_display = self.result_label

        cv2.putText(img, label_to_display, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# WebRTC: 실시간 카메라 표시
ctx = webrtc_streamer(
    key="face-recognition",
    mode=WebRtcMode.SENDRECV,
    media_stream_constraints={"video": True, "audio": False},
    video_processor_factory=VideoProcessor,
    async_processing=True,
)

# ===== 우측 패널에 최신 응답을 '계속' 표시 (새 응답 오면 즉시 갱신) =====
# autorefresh로 가볍게 갱신(0.5초마다)
st.autorefresh(interval=500, key="live_refresh")

if ctx and ctx.video_processor:
    with ctx.video_processor.lock:
        current_label = ctx.video_processor.result_label
        current_json = ctx.video_processor.last_json

    # 라벨은 항상 표시(계속 유지)
    if current_label and current_label != "...":
        result_box.success(f"현재 결과: **{current_label}**")
    else:
        result_box.info("현재 결과 대기 중... (2초마다 전송)")

    # 원본 JSON 옵션
    if show_raw:
        raw_box.subheader("Raw Response")
        if current_json is not None:
            raw_box.json(current_json)
        else:
            raw_box.write({"info": "아직 응답 없음"})
else:
    result_box.info("카메라 권한을 허용하면 실시간 화면이 표시됩니다.")
    raw_box.empty()
