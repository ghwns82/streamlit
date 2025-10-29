import time
import json
import threading
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import requests
import cv2
import av
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase

# ===== 공통 UI 구성 (당신이 준 코드 스타일 유지) =====
st.set_page_config(page_title="얼굴 식별(실시간)", page_icon="🧑‍💼")

st.title("🧑‍💼 얼굴 식별 (실시간)")
st.caption("실시간 카메라 프레임을 2초에 1번 FastAPI로 보내서 누구인지 확인합니다.")

API_URL = "https://fastapi-3uqk.onrender.com/predict"  # 당신이 준 코드 그대로 사용
show_raw = st.checkbox("서버 원본 응답(JSON)도 표시", value=False)

# 결과 표시 영역(표/메시지용)
result_placeholder = st.empty()
raw_placeholder = st.empty()

# ===== 응답 파서 (당신 코드의 로직을 실시간 버전에 맞게 재사용) =====
def parse_response(data: Any) -> Tuple[Optional[str], Optional[float], Optional[List[Dict[str, Any]]]]:
    """
    1) {"name": "...", "confidence": 0.97}
    2) {"predictions": [{"name": "...", "confidence": 0.97}, ...]}
    3) {"id": "...", "score": 0.97}
    등 다양한 스키마를 유연하게 처리
    """
    name = None
    conf = None
    candidates = None

    if isinstance(data, dict):
        # {"id": "...", "score": ...}
        if "id" in data:
            name = data.get("id")
            conf = data.get("score")

        # {"name": "...", "confidence": ...}
        if name is None and "name" in data:
            name = data.get("name")
            if conf is None:
                conf = data.get("confidence")

        # {"predictions": [ ... ]}
        if "predictions" in data and isinstance(data["predictions"], list) and data["predictions"]:
            candidates = data["predictions"]

    return name, conf, candidates

# ===== WebRTC 비디오 프로세서 =====
class VideoProcessor(VideoProcessorBase):
    SEND_INTERVAL = 2.0  # 최소 2초에 1번만 전송 (요구사항)

    def __init__(self):
        self.last_sent_ts = 0.0
        self.lock = threading.Lock()
        self.last_result: Optional[Dict[str, Any]] = None   # 서버 원본 응답 저장
        self.parsed: Tuple[Optional[str], Optional[float], Optional[List[Dict[str, Any]]]] = (None, None, None)

    def _post_frame(self, img_bgr):
        ok, jpg = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            return
        files = {"file": ("frame.jpg", jpg.tobytes(), "image/jpeg")}
        try:
            resp = requests.post(API_URL, files=files, timeout=10)
            if not resp.ok:
                data = {"error": f"HTTP {resp.status_code}", "text": resp.text}
            else:
                data = resp.json()
            name, conf, cands = parse_response(data)
            with self.lock:
                self.last_result = data
                self.parsed = (name, conf, cands)
        except requests.exceptions.RequestException as e:
            with self.lock:
                self.last_result = {"error": "network", "message": str(e)}
                self.parsed = (None, None, None)

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        # 2초(고정) 간격으로만 서버에 전송
        now = time.time()
        if now - self.last_sent_ts >= self.SEND_INTERVAL:
            self.last_sent_ts = now
            threading.Thread(target=self._post_frame, args=(img.copy(),), daemon=True).start()

        # 최근 결과를 프레임에 오버레이 (텍스트)
        with self.lock:
            name, conf, cands = self.parsed

        h, w = img.shape[:2]
        y0 = 30
        dy = 28

        def put(line, y, color=(0, 255, 0)):
            cv2.putText(img, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)

        if name:
            line = f"Result: {name}"
            if isinstance(conf, (int, float)):
                line += f" (conf: {conf:.3f})"
            put(line, y0)
        elif cands:
            put("Candidates:", y0)
            for i, c in enumerate(cands[:3]):
                nm = c.get("name") or c.get("identity") or "unknown"
                sc = c.get("confidence") or c.get("score")
                if isinstance(sc, (int, float)):
                    put(f"- {nm} ({sc:.3f})", y0 + (i + 1) * dy)
                else:
                    put(f"- {nm}", y0 + (i + 1) * dy)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# ===== WebRTC 위젯 =====
ctx = webrtc_streamer(
    key="realtime-identify",
    mode=WebRtcMode.SENDRECV,
    media_stream_constraints={"video": True, "audio": False},
    video_processor_factory=VideoProcessor,
    async_processing=True,
)

# ===== 페이지 하단: 당신 코드 스타일의 결과 표시 (표/JSON) =====
if ctx and ctx.video_processor:
    with ctx.video_processor.lock:
        data = ctx.video_processor.last_result
        name, conf, candidates = ctx.video_processor.parsed

    # 표준화된 표시 (당신 코드 방식)
    if data is None:
        result_placeholder.info("아직 서버 응답이 없습니다. (최소 2초 간격으로 요청)")
        raw_placeholder.empty()
    else:
        # 해석 가능한 단일 결과
        if name:
            if isinstance(conf, (int, float)):
                result_placeholder.success(f"식별 결과: **{name}** (confidence: {conf:.3f})")
            else:
                result_placeholder.success(f"식별 결과: **{name}**")
        # 후보 리스트
        elif candidates:
            rows = []
            for c in candidates[:5]:
                rows.append({
                    "name": c.get("name") or c.get("identity") or "unknown",
                    "confidence": c.get("confidence") or c.get("score"),
                })
            result_placeholder.subheader("후보 결과 (상위 5)")
            result_placeholder.dataframe(rows, use_container_width=True)
        else:
            # 에러 메시지 또는 미해석 응답
            if isinstance(data, dict) and data.get("error"):
                result_placeholder.error(f"요청 실패: {data.get('error')} - {data.get('message') or data.get('text')}")
            else:
                result_placeholder.warning("응답을 해석할 수 없습니다. 서버 응답 스키마를 확인하세요.")

        # 원본 JSON 표시 옵션
        if show_raw:
            try:
                raw_placeholder.subheader("Raw Response")
                raw_placeholder.json(data)
            except Exception:
                raw_placeholder.write(data)
        else:
            raw_placeholder.empty()
else:
    result_placeholder.info("카메라 권한을 허용하면 실시간 전송이 시작됩니다.")
    raw_placeholder.empty()
