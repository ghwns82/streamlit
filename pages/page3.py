import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import threading, requests, cv2, av, time

API_URL = "https://your.api.endpoint/predict"
SEND_EVERY_N_FRAMES = 30

st.set_page_config(page_title="📷 Webcam + API", layout="wide")
st.title("📷 실시간 웹캠 → API 응답 표시")

# 0) 주기적 갱신(0.5초) - 필요 없으면 지워도 됨
st.autorefresh(interval=500, key="live_refresh")

result_placeholder = st.empty()
status_placeholder = st.empty()  # 상태/오류 출력용

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
                raise RuntimeError("cv2.imencode failed")
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
            # 화면에 예외 원인을 바로 띄우기
            st.exception(e)
            res = {"id": "exception", "score": str(e)}
        finally:
            with self.lock:
                self.latest_result = res

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1

        # N프레임마다 API 호출 (백그라운드)
        if self.frame_count % SEND_EVERY_N_FRAMES == 0 and (time.time()-self._last_sent) > 0.5:
            self._last_sent = time.time()
            threading.Thread(target=self._send, args=(img.copy(),), daemon=True).start()

        # 비디오 오버레이
        with self.lock:
            label = f"{self.latest_result['id']} ({self.latest_result['score']})"
        cv2.rectangle(img, (10,10), (420,70), (0,0,0), -1)
        cv2.putText(img, label, (20,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        return av.VideoFrame.from_ndarray(img, format="bgr24")

ctx = webrtc_streamer(
    key="live_cam",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    media_stream_constraints={"video": True, "audio": False},
)

# ⛔ while True 금지: rerun 구조에 맞게, 렌더 한 번에 '현재 상태'만 보여줌
try:
    vp = getattr(ctx, "video_processor", None)
    if vp is not None:
        with vp.lock:
            r = dict(vp.latest_result)
        result_placeholder.markdown(f"**🧠 ID:** `{r['id']}`  |  **Score:** `{r['score']}`")
        status_placeholder.info("🎥 스트리밍 중")
    else:
        result_placeholder.markdown("**🧠 ID:** `-`  |  **Score:** `-`")
        status_placeholder.warning("⏳ 스트림 대기/중지 상태")
except AttributeError as e:
    # 혹시 모를 접근 타이밍 이슈도 화면에 바로 표시
    st.exception(e)
