import streamlit as st
import requests
import datetime as dt
import calendar
from config import BACK_URL

st.set_page_config(page_title="월별 출석 확인", page_icon="📅")
st.title("📅 월별 출석 확인")

API_BASE = BACK_URL.rstrip("/")
ATTEND_API = f"{API_BASE}/attendance"

# ---------------------------
# 1️⃣ 검색 전 정보 입력
# ---------------------------
with st.form("query_form"):
    name = st.text_input("이름 (선택, 영문 권장)")
    ID = st.text_input("학번 (필수)")
    
    col_t1, col_t2 = st.columns(2)
    start_time = col_t1.time_input("시작 시각 (없으면 00:00)", value=None)
    end_time = col_t2.time_input("종료 시각 (없으면 23:59)", value=None)

    col_d1, col_d2 = st.columns(2)
    today = dt.date.today()
    start_date = col_d1.date_input("조회 시작일", value=today.replace(day=1))
    end_date = col_d2.date_input("조회 종료일", value=today)

    submitted = st.form_submit_button("출석 달력보기")

# ---------------------------
# 2️⃣ API 통신
# ---------------------------
def fetch_attendance(ID, name, start_date, end_date, start_time, end_time):
    if not ID:
        st.warning("학번은 필수입니다.")
        return []

    # 시간 범위 기본값 (24시간 전체)
    start_t = start_time.strftime("%H:%M:%S") if start_time else "00:00:00"
    end_t = end_time.strftime("%H:%M:%S") if end_time else "23:59:59"

    data = {"ID": ID}

    try:
        with st.spinner("출석 데이터 조회 중..."):
            resp = requests.post(ATTEND_API, data=data, timeout=30)
        if not resp.ok:
            st.error(f"서버 오류: {resp.status_code} {resp.text}")
            return []
        data = resp.json()
        rows = data.get("rows", [])
        return rows
    except requests.exceptions.RequestException as e:
        st.error(f"네트워크 오류: {e}")
        return []

# ---------------------------
# 3️⃣ 달력 렌더링
# ---------------------------
def render_calendar(start_date: dt.date, end_date: dt.date, attend_rows: list):
    """
    timestamp에서 초는 제거하고 (시:분)까지만 사용,
    같은 날짜에 여러 출석 기록이 있으면 1회만 표시.
    """
    # 출석 데이터 전처리
    attendance = {}
    for row in attend_rows:
        ts = row.get("timestamp")
        if not ts:
            continue
        # 2025-11-03 17:23:37 → 날짜 + 시:분
        date_part, time_part = ts.split(" ")
        hour, minute = time_part.split(":")[:2]
        display_time = f"{hour}:{minute}"
        d = dt.date.fromisoformat(date_part)
        # 중복 제거
        if d not in attendance:
            attendance[d] = []
        if display_time not in attendance[d]:
            attendance[d].append(display_time)

    st.markdown("""
        <style>
        .cal-wrap { margin: 1rem 0 2rem 0; }
        .cal-title { font-weight: 700; margin: 0.5rem 0; }
        .cal-row { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }
        .cal-cell {
            border: 1px solid #e5e7eb; border-radius: 8px;
            padding: 6px; min-height: 56px; text-align: center;
            background: #fff; font-size: 14px;
        }
        .cal-head { font-weight: 600; background: #f8fafc; }
        .cal-day-on  { background: #ecfdf5; border-color: #34d399; }
        .time-list { font-size: 11px; color: #047857; margin-top: 4px; line-height: 1.2em; }
        .cal-day-off { color: #9ca3af; }
        </style>
    """, unsafe_allow_html=True)

    week_headers = ["월", "화", "수", "목", "금", "토", "일"]

    # start~end 사이 월 단위 반복
    first = start_date.replace(day=1)
    last = end_date.replace(day=1)
    y, m = first.year, first.month

    while (y < last.year) or (y == last.year and m <= last.month):
        st.markdown(f"<div class='cal-wrap'><div class='cal-title'>📆 {y}년 {m}월</div>", unsafe_allow_html=True)
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(y, m)

        # 헤더
        head_html = "<div class='cal-row'>" + "".join(
            f"<div class='cal-cell cal-head'>{w}</div>" for w in week_headers
        ) + "</div>"
        st.markdown(head_html, unsafe_allow_html=True)

        # 날짜 렌더링
        rows_html = ""
        for week in month_days:
            rows_html += "<div class='cal-row'>"
            for day in week:
                if day == 0:
                    rows_html += "<div class='cal-cell cal-day-off'>&nbsp;</div>"
                else:
                    d = dt.date(y, m, day)
                    # 기간 밖
                    if d < start_date or d > end_date:
                        rows_html += f"<div class='cal-cell cal-day-off'>{day}</div>"
                    else:
                        if d in attendance:
                            times_html = "<br>".join(attendance[d])
                            rows_html += f"<div class='cal-cell cal-day-on'>{day}<div class='time-list'>{times_html}</div></div>"
                        else:
                            rows_html += f"<div class='cal-cell'>{day}</div>"
            rows_html += "</div>"
        st.markdown(rows_html + "</div>", unsafe_allow_html=True)

        if m == 12:
            y += 1
            m = 1
        else:
            m += 1

# ---------------------------
# 4️⃣ 실행 흐름
# ---------------------------
if submitted:
    if not ID:
        st.error("학번은 필수입니다.")
    else:
        rows = fetch_attendance(ID, name, start_date, end_date, start_time, end_time)
        if rows:
            st.success(f"총 {len(rows)}건의 출석 데이터 수신 ✅")
        render_calendar(start_date, end_date, rows)
