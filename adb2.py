import streamlit as st
import google.generativeai as genai
import requests
import base64
from datetime import datetime
import os
import json

# --- 1. API 키 저장/불러오기 설정 ---
KEY_FILE = "keys.json"
ADMIN_PASSWORD = "1234" # 관리자 비밀번호 (변경 가능)

def save_keys(g_key, e_key):
    with open(KEY_FILE, "w") as f:
        json.dump({"gemini": g_key, "eleven": e_key}, f)

def load_keys():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            return json.load(f)
    return None

# 저장된 키 로드
saved_data = load_keys()
GEMINI_API_KEY = saved_data["gemini"] if saved_data else ""
ELEVENLABS_API_KEY = saved_data["eleven"] if saved_data else ""

# --- 2. 사이드바 구성 (관리자 로그인 + 채팅 관리) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("⚙️ 시스템 설정")
    
    # [A] 관리자 전용 키 설정
    with st.expander("🔐 관리자 로그인 (API 등록)"):
        admin_pw = st.text_input("비밀번호 입력", type="password")
        if admin_pw == ADMIN_PASSWORD:
            st.success("인증되었습니다.")
            new_g_key = st.text_input("Gemini API 키", value=GEMINI_API_KEY)
            new_e_key = st.text_input("ElevenLabs API 키", value=ELEVENLABS_API_KEY)
            if st.button("서버에 설정 저장"):
                save_keys(new_g_key, new_e_key)
                st.success("모든 사용자에게 적용되었습니다!")
                st.rerun()
        elif admin_pw:
            st.error("비밀번호가 틀렸습니다.")

    st.divider()

    # [B] 채팅 관리 기능 (다시 추가됨)
    st.subheader("💬 채팅 관리")
    if st.button("🗑️ 전체 대화 삭제"):
        st.session_state.messages = []
        st.rerun()

    # 대화 다운로드 로직
    chat_text = "\n".join([f"[{m['role'].upper()}] {m['content']}" for m in st.session_state.messages])
    st.download_button(
        label="💾 대화 내용 다운로드",
        data=chat_text,
        file_name=f"초록_대화기록_{datetime.now().strftime('%m%d_%H%M')}.txt",
        mime="text/plain"
    )

# --- 3. API 초기화 체크 ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.warning("⚠️ 서버에 등록된 API 키가 없습니다. 관리자 설정을 먼저 완료해주세요.")
    st.stop()

# 고정값 설정
VOICE_ID = "dHC7jAYDvo5m8CkyQZnL"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1461850433458016308/6olE8TMTSyKgM81_p5BdA8ZtrnL1uo5NyD1Y7Yt8F-taUM_v1KfnRUCNV4FoiCRerBYQ"

# --- 4. 다크 모드 디자인 ---
st.set_page_config(page_title="AI 비서 초록", page_icon="🟢")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .user-bubble { background-color: #fee500; padding: 12px; border-radius: 15px; margin-bottom: 10px; display: inline-block; float: right; clear: both; color: #000000 !important;
