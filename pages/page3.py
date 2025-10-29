# app.py (핵심 부분만)
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import threading, requests, cv2, av, time

API_URL = "https://your.api.endpoint/predict"
SEND_EVERY_N_FRAMES = 30

st.set_page_config(page_title="📷 Webcam + API", layout="wide")
st.title("📷 실시간 웹캠 → API 응답 표시")

# 0. 주기적 리렌더링(0.5초마다)로 최신 값 표시
st.autorefresh(interval=500, key="live_refresh")

# 1) 결과 보여줄 자리
result_placeholder = st.empty()

class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame_count = 0
        self.lock = threading.Lock()
        self.latest_result = {"id": "...", "score": "..."}
        self._last_sent = 0.0

    def _send(self, bgr):
        try:
            ok, buf = cv2.imencode(".jpg", bgr)
            if not ok:
                return
            r = requests.post(
                API_URL,
                files={"file": ("frame.jpg", buf.tobytes(), "image/jpeg")},
                timeout=6,
            )
            if r.status_code == 200:
                data = r.json()
                res = {"id": data.get("id", "unknown"),
                       "score": data.get("score", 0.0)}
            else:
                res = {"id": f"HTTP{r.status_code}", "score": 0}
        except Exception as e:
            res = {"id": "exception", "score": str(e)}

        with self.lock:
            self.latest_result = res

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1
        if self.frame_count % SEND_EVERY_N_FRAMES == 0 and (time.time()-self._last_sent) > 0.5:
            self._last_sent = time.time()
            threading.Thread(target=self._send, args=(img.copy(),), daemon=True).start()

        # 비디오 오버레이
        with self.lock:
            label = f"{self.latest_result['id']} ({self.latest_result['score']})"
        cv2.rectangle(img, (10,10), (380,70), (0,0,0), -1)
        cv2.putText(img, label, (20,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        return av.VideoFrame.from_ndarray(img, format="bgr24")

ctx = webrtc_streamer(
    key="live_cam",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False},
)

# 2) 오른쪽(혹은 아래) 패널에 최신 응답 표시 (❌ while True 금지)
vp = getattr(ctx, "video_processor", None)
if vp is not None:
    with vp.lock:
        r = dict(vp.latest_result)
    result_placeholder.markdown(f"**🧠 ID:** `{r['id']}`  |  **Score:** `{r['score']}`")
else:
    result_placeholder.markdown("**🧠 ID:** `-`  |  **Score:** `-`  _(스트림 대기/중지)_")
