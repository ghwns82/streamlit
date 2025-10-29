# app.py
import threading
import time
import cv2
import av
import numpy as np
import requests
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode

API_URL = "https://fastapi-3uqk.onrender.com/predict" # <- 여기에 본인 API 주소
SEND_EVERY_N_FRAMES = 30                       # N프레임마다 전송

st.set_page_config(page_title="Webcam → API", page_icon="📷")
st.title("📷 Streamlit Webcam → API (minimal)")

class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame_count = 0
        self.lock = threading.Lock()
        self.latest_result = "..."
        self.last_sent_ts = 0.0

    def _post_frame(self, bgr_img: np.ndarray):
        try:
            ok, buf = cv2.imencode(".jpg", bgr_img)
            if not ok:
                return
            resp = requests.post(
                API_URL,
                files={"file": ("frame.jpg", buf.tobytes(), "image/jpeg")},
                timeout=8,
            )
            if resp.status_code == 200:
                data = resp.json()
                # 예: {"predictions":{"ResNet18":"Alice"}}
                label = (data.get("predictions") or {}).get("ResNet18", "OK")
            else:
                label = f"HTTP {resp.status_code}"
        except Exception as e:
            label = f"ERR: {e}"

        with self.lock:
            self.latest_result = str(label)

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1

        # N프레임마다 전송 (너무 자주 안보내도록 간단한 쿨다운 추가)
        if self.frame_count % SEND_EVERY_N_FRAMES == 0 and (time.time() - self.last_sent_ts) > 0.5:
            self.last_sent_ts = time.time()
            threading.Thread(target=self._post_frame, args=(img.copy(),), daemon=True).start()

        # 결과 오버레이
        with self.lock:
            text = self.latest_result

        cv2.rectangle(img, (10, 10), (320, 70), (0, 0, 0), -1)
        cv2.putText(img, f"Result: {text}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

webrtc_streamer(
    key="webcam",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False},
)
