import streamlit as st
from streamlit_webrtc import webrtc_streamer
import os

st.set_page_config(page_title="카메라 미리보기", page_icon="📷")
st.title("📷 카메라 미리보기 (디버그)")

# 원격 환경에서는 STUN 서버 지정이 도움이 됩니다.
RTC_CONFIGURATION = {
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
}

webrtc_streamer(
    key="cam-preview",
    media_stream_constraints={
        "video": {
            # 전면 카메라 선호 (모바일)
            "facingMode": "user",
            # 너무 높은 해상도 요구하면 장치가 못 열 수 있으니 적당히
            "width": {"ideal": 1280},
            "height": {"ideal": 720},
            # 특정 장치를 강제하고 싶다면 deviceId를 exact로 지정 가능
            # "deviceId": {"exact": "<YOUR_DEVICE_ID>"},
        },
        "audio": False,
    },
    rtc_configuration=RTC_CONFIGURATION,
)
