import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import threading, requests, cv2, av, time

API_URL = "https://fastapi-3uqk.onrender.com/predict"
   # ⚙️ 여기에 API 주소
SEND_EVERY_N_FRAMES = 30                        # 몇 프레임마다 전송할지 설정

st.set_page_config(page_title="📷 Webcam + API", layout="wide")
st.title("📷 실시간 웹캠 → API 응답 표시")
class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame_count = 0
        self.latest_result = {"id": "...", "score": "..."}
        self.lock = threading.Lock()
        self.last_sent_time = 0.0

    def send_frame_to_backend(self, img):
        try:
            _, img_encoded = cv2.imencode('.jpg', img)
            response = requests.post(
                API_URL,
                files={"file": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")},
                timeout=10  # ✅ 더 넉넉하게
            )
            if response.status_code == 200:
                data = response.json()
                with self.lock:
                    self.latest_result = {
                        "id": data.get("id", "unknown"),
                        "score": data.get("score", 0.0),
                    }
            else:
                with self.lock:
                    self.latest_result = {"id": "error", "score": 0}

        except Exception as e:
            with self.lock:
                self.latest_result = {"id": "exception", "score": str(e)}

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1

        if self.frame_count % self.request_interval == 0:
            threading.Thread(target=self.send_frame_to_backend, args=(img.copy(),)).start()

        with self.lock:
            label = f"{self.latest_result['id']} ({self.latest_result['score']})"

        cv2.putText(img, label, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
        return frame.from_ndarray(img, format="bgr24")

webrtc_streamer(key="face-recognition", video_processor_factory=VideoProcessor)