import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode

st.title("🎥 실시간 카메라 화면")

webrtc_streamer(
    key="camera",
    mode=WebRtcMode.SENDRECV,
    media_stream_constraints={"video": True, "audio": False},
)
