import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import threading, requests, cv2, av, time
from config import BACK_URL


API_URL =BACK_URL+'/predict'
SEND_EVERY_N_FRAMES = 100                        # 몇 프레임마다 전송할지 설정

st.title("📷 실시간 카메라로 확인")
class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame_count = 0
        self.result_label = "..."
        self.request_interval = SEND_EVERY_N_FRAMES
        self.lock = threading.Lock()

    def send_frame_to_backend(self, img):
        try:
            _, img_encoded = cv2.imencode('.jpg', img)
            response = requests.post(
                API_URL,
                files={"file": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")},
                timeout=100  # ✅ 더 넉넉하게
            )
            if response.status_code == 200:
                result = response.json()
                print('success',result)
                label = result.get("student_name", "unknown") 
            elif response.status_code == 204:
                label = '...' 
            else:
                label = "Many People"
                print(response.json())
        except Exception as e:
            print("🔥 예외 발생:", e)  # ✅ 콘솔에 에러 메시지 출력
            label = "Error except"

        with self.lock:
            self.result_label = label

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1

        if self.frame_count % self.request_interval == 0:
            threading.Thread(target=self.send_frame_to_backend, args=(img.copy(),)).start()

        with self.lock:
            label_to_display = self.result_label

        cv2.putText(img, label_to_display, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
        return frame.from_ndarray(img, format="bgr24")

webrtc_streamer(key="face-recognition", video_processor_factory=VideoProcessor,
        media_stream_constraints={
        "video": {
            "facingMode": "user"       # 전면카메라 (모바일)
        },
        "audio": False,
    },)