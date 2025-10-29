import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import threading, requests, cv2, av, time

API_URL = "https://fastapi-3uqk.onrender.com/predict"   # ⚙️ 여기에 API 주소
SEND_EVERY_N_FRAMES = 30                        # 몇 프레임마다 전송할지 설정

st.set_page_config(page_title="📷 Webcam + API", layout="wide")
st.title("📷 실시간 웹캠 → API 응답 표시")

# 오른쪽 패널에 표시될 placeholder
result_placeholder = st.empty()

class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame_count = 0
        self.lock = threading.Lock()
        self.latest_result = {"id": "...", "score": "..."}
        self.last_sent_time = 0.0

    def send_frame(self, frame_bgr):
        try:
            ok, buf = cv2.imencode(".jpg", frame_bgr)
            if not ok:
                return
            res = requests.post(
                API_URL,
                files={"file": ("frame.jpg", buf.tobytes(), "image/jpeg")},
                timeout=5,
            )
            if res.status_code == 200:
                data = res.json()
                # {"id": "person1", "score": 0.92} 같은 형태라고 가정
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

        # N프레임마다 API로 전송 (별도 스레드로 처리)
        if self.frame_count % SEND_EVERY_N_FRAMES == 0 and (time.time() - self.last_sent_time) > 0.5:
            self.last_sent_time = time.time()
            threading.Thread(target=self.send_frame, args=(img.copy(),), daemon=True).start()

        # 최신 결과를 오버레이
        with self.lock:
            label = f"{self.latest_result['id']} ({self.latest_result['score']})"
        cv2.rectangle(img, (10, 10), (350, 70), (0, 0, 0), -1)
        cv2.putText(img, label, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

ctx = webrtc_streamer(
    key="live_cam",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False},
)

# 오른쪽 패널에 실시간 결과 표시
if ctx and ctx.video_processor:
    while True:
        with ctx.video_processor.lock:
            result = ctx.video_processor.latest_result
        result_placeholder.markdown(
            f"**🧠 ID:** `{result['id']}`  |  **Score:** `{result['score']}`"
        )
        time.sleep(0.5)
