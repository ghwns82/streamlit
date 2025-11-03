import streamlit as st
import glob,os

st.set_page_config(page_title="메인 페이지", page_icon="🏠")

# --- 내비게이션 정의 ---
pages = {}
for path in sorted(glob.glob('./pages/*')): 
    if not os.path.isdir(path):
        continue
    menu = path.replace('./pages/','')
    pages[menu] = []
    for file_path in sorted(glob.glob(path+'/*')):
        file = os.path.split(file_path)[1]
        page = st.Page(file_path, title=file[:-3].replace('_',' '))
        pages[menu].append(page)


pg = st.navigation(pages)
pg.run()


