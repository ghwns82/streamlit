import streamlit as st
import glob,os

st.set_page_config(page_title="메인 페이지", page_icon="🏠")
st.title("🏠 얼굴 인식 출석 시스템")
st.subheader("메인 페이지")
st.write("아래에서 원하는 기능을 선택하세요 👇")

for path in sorted(glob.glob('./pages/*')): 
    if not os.path.isdir(path):
        continue
    menu = path.replace('./pages/','')[2:]
    if '홈' in menu:
        continue
    st.subheader(menu)
    files = sorted(glob.glob(path+'/*'))

    for col, file_path in zip(st.columns(len(files)), files):
        with col:
            file = os.path.split(file_path)[1]
            title = file[:-3].replace('_',' ')
            if st.button(title):
                st.switch_page(file_path)
    st.divider()




# st.subheader('얼굴 등록')
# col1, col2 = st.columns(2)

# with col1:
#     if st.button("📘 얼굴 등록"):
#         st.switch_page("pages/page1.py")
# with col2:
#     if st.button("📘 얼굴 등록2"):
#         st.switch_page("pages/paget.py")

# st.divider()

# st.subheader('얼굴 검사')
# col3, col4 = st.columns(2)

# with col3:
#     if st.button("📗 얼굴 검사"):
#         st.switch_page("pages/page2.py")


# with col4:
#     if st.button("📗 얼굴 검사2"):
#         st.switch_page("pages/page3.py")

# st.divider()

# st.subheader('출석체크')
# if st.button("📗 출석체크"):
#     st.switch_page("pages/page4.py")


