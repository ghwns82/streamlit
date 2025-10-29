# app_live_2sec_api.py
import time
import json
import threading
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import requests
import cv2
import av
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase

st.set_page_config(page_title="실시간 얼굴 식별", page_icon="🧑‍💼")
st.title("🧑‍💼 실시간 얼굴 식별")
st.caption("실시간 카메라를 표시하고, 2초마다 FastAPI로 전송하여 결과를 표시합니다.")

API_URL = "https://fastapi-3uqk.onrender.com/predict"  # 기존 스타일 유지
show_raw = st.checkbox("서버 원본 응답(JSON)도 표시", value=False)

result_box = st.empty()
raw_box = st.empty()

def parse_response(data: Any) -> Tuple[Optional[str], Optional[float], Optional[List[Dict[str, Any]]]]:
    name = None
    conf = None
    candidates = None
    if isinstance(data, dict):
        if "id" in data:
            name = data.get("id"); conf = data.get("score")
        if name is None and "name" in data:
            name = data.get("name"); conf = data.get("confidence") if conf is None else conf
        if "predictions" in data and isinstance(data["predictions"], list) and data["predictions"]:
            candidates = data["predictions"]
    return name, conf, candidates

class VideoProcessor(VideoProcessorBase):
    SEND_INTERVAL = 2.0  # 2초마다 전송

    def __init__(self):
        self.last_sent = 0.0
        self.lock = threading.Lock()
        self.last_result: Optional[Dict[str, Any]] = None
        self.parsed: Tuple[Optional[str], Optional[float], Optional[List[Dict[str, Any]]]] = (None, None, None)

    def _post(self, img_bgr):
        ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            return
        try:
            files = {"file": ("frame.jpg", buf.tobytes(), "image/jpeg")}
            r = requests.post(API_URL, files=files, timeout=10)
            data = r.json() if r.ok else {"error": f"HTTP {r.status_code}", "text": r.text}
        except requests.exceptions.RequestException as e:
            data = {"error": "network", "message": str(e)}

        name, conf, cands = parse_response(data)
        with self.lock:
            self.last_result = data
            self.parsed = (name, conf, cands)

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        now = time.time()
        if now - self.last_sent >= self.SEND_INTERVAL:
            self.last_sent = now
            threading.Thread(target=self._post, args=(img.copy(),), daemon=True).start()

        # 오버레이
        with self.lock:
            name, conf, cands = self.parsed
        y0, dy = 30, 28
        def put(t, y, col=(0,255,0)): cv2.putText(img, t, (10,y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, col, 2, cv2.LINE_AA)
        if name:
            txt = f"Result: {name}" + (f" (conf: {conf:.3f})" if isinstance(conf,(int,float)) else "")
            put(txt, y0)
        elif cands:
            put("Candidates:", y0)
            for i, c in enumerate(cands[:3]):
                nm = c.get("name") or c.get("identity") or "unknown"
                sc = c.get("confidence") or c.get("score")
                put(f"- {nm}" + (f" ({sc:.3f})" if isinstance(sc,(int,float)) else ""), y0+(i+1)*dy)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

ctx = webrtc_streamer(
    key="live-2sec-api",
    mode=WebRtcMode.SENDRECV,
    media_stream_constraints={"video": True, "audio": False},
    video_processor_factory=VideoProcessor,
    async_processing=True,
)

# 결과 패널
if ctx and ctx.video_processor:
    with ctx.video_processor.lock:
        data = ctx.video_processor.last_result
        name, conf, cands = ctx.video_processor.parsed

    if data is None:
        result_box.info("아직 응답 없음 (2초마다 전송)")
        raw_box.empty()
    else:
        if name:
            msg = f"식별 결과: **{name}**" + (f" (confidence: {conf:.3f})" if isinstance(conf,(int,float)) else "")
            result_box.success(msg)
        elif cands:
            rows = [{"name": c.get("name") or c.get("identity") or "unknown",
                     "confidence": c.get("confidence") or c.get("score")} for c in cands[:5]]
            result_box.subheader("후보 결과 (상위 5)")
            result_box.dataframe(rows, use_container_width=True)
        else:
            if isinstance(data, dict) and data.get("error"):
                result_box.error(f"요청 실패: {data.get('error')} - {data.get('message') or data.get('text')}")
            else:
                result_box.warning("응답을 해석할 수 없습니다. 서버 스키마 확인 필요.")

        if show_raw:
            raw_box.subheader("Raw Response")
            raw_box.json(data)
        else:
            raw_box.empty()
else:
    result_box.info("카메라 권한 허용 후 시작됩니다.")
    raw_box.empty()
