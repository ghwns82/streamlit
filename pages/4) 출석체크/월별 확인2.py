import streamlit as st
import requests
import os
import datetime as dt
import calendar
from config import BACK_URL

st.set_page_config(page_title="출석체크", page_icon="📤")
st.title("🕒 출석 관리")

API_BASE = BACK_URL.rstrip("/")
ATTEND_API = f"{API_BASE}/attendance"

# ---------------------------
# 1) 출석 인정 시간 범위 설정
# ---------------------------
with st.expander("⏱️ 출석 인정 시간 범위 설정", expanded=True):
    col_t1, col_t2 = st.columns(2)
    start_time = col_t1.time_input("시작 시각", value=dt.time(9, 0))
    end_time = col_t2.time_input("종료 시각", value=dt.time(9, 30))
    if start_time >= end_time:
        st.error("출석 인정 시작 시각이 종료 시각보다 같거나 늦을 수 없습니다.")

    with st.form("upload_form"):
        name = st.text_input("이름 (선택, 영문 권장)")
        student_id = st.text_input("학번 (필수)")
        submitted = st.form_submit_button("전송")

# ---------------------------
# 3) 달력으로 출석 현황 보기
# ---------------------------
st.subheader("📅 달력으로 출석 확인")

# 기본 조회 기간: 최근 30일
today = dt.date.today()
default_start = today - dt.timedelta(days=30)

col_d1, col_d2, col_btn = st.columns([1,1,0.6])
start_date = col_d1.date_input("조회 시작일", value=default_start)
end_date = col_d2.date_input("조회 종료일", value=today)
do_query = col_btn.button("출석 달력 보기")

def fetch_attendance_dates(student_id: str, start_date: dt.date, end_date: dt.date):
    """
    백엔드 조회 API 시도 순서:
    1) GET /attendance/logs?student_id=...&start=YYYY-MM-DD&end=YYYY-MM-DD
    2) GET /attendance?student_id=...&start=YYYY-MM-DD&end=YYYY-MM-DD
    반환: set[date]  (출석 True인 날짜 집합)
    """
    if not student_id:
        st.warning("학번을 먼저 입력하세요.")
        return set()

    params = {
        "student_id": student_id,
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "start_time": start_time.strftime("%H:%M:%S"),
        "end_time": end_time.strftime("%H:%M:%S"),
    }

    # # 1안: /attendance/logs
    # try:
    #     r1 = requests.get(f"{ATTEND_API}/logs", params=params, timeout=30)
    #     if r1.ok:
    #         data = r1.json()
    #         # 예상 형태 예시:
    #         # [{"timestamp":"2025-11-01T09:12:00","present":true}, ...]
    #         dates = set()
    #         for item in data:
    #             present = item.get("present", True)
    #             ts = item.get("timestamp") or item.get("date")
    #             if not ts:
    #                 continue
    #             # 날짜 파싱
    #             date_str = ts[:10]  # "YYYY-MM-DD"
    #             d = dt.date.fromisoformat(date_str)
    #             if present:
    #                 dates.add(d)
    #         return dates
    # except requests.exceptions.RequestException:
    #     pass

    # 2안: /attendance  (GET)
    try:
        r2 = requests.get(ATTEND_API, params=params, timeout=30)
        if r2.ok:
            data = r2.json()
            dates = set()
            for item in data:
                present = item.get("present", True)
                ts = item.get("timestamp") or item.get("date")
                if not ts:
                    continue
                date_str = ts[:10]
                d = dt.date.fromisoformat(date_str)
                if present:
                    dates.add(d)
            return dates
    except requests.exceptions.RequestException:
        pass

    st.info("출석 조회 API가 필요합니다. `/attendance/logs` 또는 `/attendance`(GET) 형태를 제공해주세요.")
    return set()

def render_calendar(start_date: dt.date, end_date: dt.date, present_dates: set[dt.date]):
    """
    조회 기간에 포함되는 각 '월' 단위로 달력을 그려서
    present_dates에 포함된 날짜에 ✅ 마크 표시.
    """
    # 스타일(살짝 보기 좋게)
    st.markdown("""
        <style>
        .cal-wrap { margin: 0.5rem 0 2rem 0; }
        .cal-title { font-weight: 700; margin: 0.5rem 0; }
        .cal-row { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }
        .cal-cell {
            border: 1px solid #e5e7eb; border-radius: 8px;
            padding: 8px; min-height: 48px; text-align: center; background: #fff;
        }
        .cal-head { font-weight: 600; background: #f8fafc; }
        .cal-day-on  { background: #ecfdf5; border-color: #34d399; }
        .cal-day-off { color: #9ca3af; }
        </style>
    """, unsafe_allow_html=True)

    # 요일 헤더
    week_headers = ["월", "화", "수", "목", "금", "토", "일"]

    # start~end 사이의 각 월을 순회
    first = start_date.replace(day=1)
    last = end_date.replace(day=1)
    y, m = first.year, first.month

    while (y < last.year) or (y == last.year and m <= last.month):
        st.markdown(f"<div class='cal-wrap'><div class='cal-title'>📆 {y}년 {m}월</div>", unsafe_allow_html=True)

        # 달력 데이터 (calendar.monthcalendar: 주 단위 2D 리스트, 0=해당 월 아님)
        cal = calendar.Calendar(firstweekday=0)  # 0=월요일
        # 우리가 표시할 건 월~일 순서라 firstweekday=0으로, 아래 헤더도 월~일로 맞춤
        month_days = cal.monthdayscalendar(y, m)

        # 헤더
        head_html = "<div class='cal-row'>" + "".join(
            f"<div class='cal-cell cal-head'>{w}</div>" for w in week_headers
        ) + "</div>"
        st.markdown(head_html, unsafe_allow_html=True)

        # 날짜 셀
        rows_html = ""
        for week in month_days:
            rows_html += "<div class='cal-row'>"
            for day in week:
                if day == 0:
                    # 다른 달의 자리
                    rows_html += "<div class='cal-cell cal-day-off'>&nbsp;</div>"
                else:
                    d = dt.date(y, m, day)
                    # 조회 범위 밖은 흐리게
                    if d < start_date or d > end_date:
                        rows_html += f"<div class='cal-cell cal-day-off'>{day}</div>"
                    else:
                        on = d in present_dates
                        cls = "cal-day-on" if on else ""
                        mark = "✅" if on else ""
                        rows_html += f"<div class='cal-cell {cls}'>{day} {mark}</div>"
            rows_html += "</div>"
        st.markdown(rows_html + "</div>", unsafe_allow_html=True)

        # 다음 달
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1

if do_query:
    if start_date > end_date:
        st.error("조회 시작일이 종료일보다 늦을 수 없습니다.")
    else:
        with st.spinner("출석 기록 조회 중..."):
            present_dates = fetch_attendance_dates(student_id, start_date, end_date)

        # 달력 렌더링
        if present_dates:
            st.success(f"출석 {len(present_dates)}일 확인됨 ✅")
        render_calendar(start_date, end_date, present_dates)
