import streamlit as st
import glob,os

st.set_page_config(page_title="메인 페이지", page_icon="🏠")

# --- 관리자 인증---
ADMIN_CODE = os.getenv("ADMIN_CODE", "1234")
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "show_code_input" not in st.session_state:
    st.session_state["show_code_input"] = False
if not st.session_state["is_admin"]:
    # 코드 입력창 보이기 토글 버튼
    if st.button("Enter admin code"):
        st.session_state["show_code_input"] = True

    if st.session_state["show_code_input"]:
        code = st.text_input("Enter admin code", type="password")

        # 코드 확인 버튼
        if st.button("Confirm code"):
            if code == ADMIN_CODE:
                st.session_state["is_admin"] = True
                st.success("Admin mode enabled ✅")
                st.session_state["show_code_input"] = False
            else:
                st.error("Invalid code ❌")

else:
    st.success("You are in admin mode ✅")

# --- 내비게이션 정의 ---
pages = {}
for i,path in enumerate(sorted(glob.glob('./pages/*'))): 
    if not os.path.isdir(path):
        continue
    if i>1 and not st.session_state["is_admin"]:
        continue
    menu = path.replace('./pages/','')
    pages[menu] = []
    
    for file_path in sorted(glob.glob(path+'/*')):
        file = os.path.split(file_path)[1]
        page = st.Page(file_path, title=file[:-3].replace('_',' '))
        pages[menu].append(page)


pg = st.navigation(pages)
pg.run()


