import streamlit as st
import google.generativeai as genai
import requests
import base64
from datetime import datetime
import os
import json

# --- 1. API 키 및 모델 설정 불러오기 ---
KEY_FILE = "keys.json"
ADMIN_PASSWORD = "1234" 

def save_keys(g_key, e_key, model_name):
    with open(KEY_FILE, "w") as f:
        json.dump({"gemini": g_key, "eleven": e_key, "model": model_name}, f)

def load_keys():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            return json.load(f)
    return None

saved_data = load_keys()
GEMINI_API_KEY = saved_data.get("gemini", "") if saved_data else ""
ELEVENLABS_API_KEY = saved_data.get("eleven", "") if saved_data else ""
# 기본 모델을 2.0-flash로 설정
SELECTED_MODEL = saved_data.get("model", "models/gemini-2.5-flash") if saved_data else "models/gemini-2.5-flash"

# --- 2. 사이드바 구성 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("⚙️ 시스템 설정")
    
    with st.expander("🔐 관리자 로그인 (API/모델 등록)"):
        admin_pw = st.text_input("비밀번호 입력", type="password")
        if admin_pw == ADMIN_PASSWORD:
            st.success("인증되었습니다.")
            new_g_key = st.text_input("Gemini API 키", value=GEMINI_API_KEY)
            new_e_key = st.text_input("ElevenLabs API 키", value=ELEVENLABS_API_KEY)
            # 모델을 직접 입력하거나 선택할 수 있게 추가
            new_model = st.selectbox("사용할 모델 선택", 
                                    ["models/gemini-2.5-flash"],
                                    index=0)
            
            if st.button("서버에 모든 설정 저장"):
                save_keys(new_g_key, new_e_key, new_model)
                st.success("모델 및 키 설정 완료!")
                st.rerun()

    st.divider()
    # 현재 적용된 모델 정보 표시
    st.info(f"🤖 현재 모델: {SELECTED_MODEL}")
    
    if st.button("🗑️ 전체 대화 삭제"):
        st.session_state.messages = []
        st.rerun()

    chat_text = "\n".join([f"[{m['role'].upper()}] {m['content']}" for m in st.session_state.messages])
    st.download_button(label="💾 대화 내용 다운로드", data=chat_text, file_name="chat_log.txt")

# --- 3. 디자인 및 모델 초기화 ---
st.set_page_config(page_title="AI 비서 초록", page_icon="🟢")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(SELECTED_MODEL) # 저장된 모델 버전 사용
else:
    st.warning("관리자 설정을 통해 API 키와 모델을 등록해주세요.")
    st.stop()

# 디자인 CSS (다크모드)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .user-bubble { background-color: #fee500; padding: 12px; border-radius: 15px; margin-bottom: 10px; display: inline-block; float: right; clear: both; color: #000000 !important; }
    .ai-container { display: flex; align-items: flex-start; margin-bottom: 10px; clear: both; }
    .profile-img { width: 45px; height: 45px; border-radius: 50%; margin-right: 10px; border: 2px solid #2e7d32; object-fit: cover; }
    .ai-bubble { background-color: #262730; padding: 12px; border-radius: 15px; display: inline-block; color: #ffffff !important; border: 1px solid #444; }
    .ai-name { font-size: 13px; color: #a0a0a0 !important; margin-bottom: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 사진 및 기타 함수 (동일)
VOICE_ID = "dHC7jAYDvo5m8CkyQZnL"
if os.path.exists("profile.jpg"):
    with open("profile.jpg", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
        PROFILE_IMG_HTML = f"data:image/jpg;base64,{img_b64}"
else:
    PROFILE_IMG_HTML = "https://cdn-icons-png.flaticon.com/512/4333/4333609.png"

def speak(text):
    if not ELEVENLABS_API_KEY: return
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        res = requests.post(url, json={"text": text, "model_id": "eleven_multilingual_v2"}, headers=headers)
        if res.status_code == 200:
            b64_audio = base64.b64encode(res.content).decode()
            st.markdown(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64_audio}"></audio>', unsafe_allow_html=True)
    except: pass

# --- 4. 채팅 화면 ---
st.title(f"🎙️ AI 비서 '초록'")
st.caption(f"현재 사용 중인 두뇌: {SELECTED_MODEL}") # 화면 상단에 모델 버전 표시

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'''<div class="ai-container"><img src="{PROFILE_IMG_HTML}" class="profile-img"><div><div class="ai-name">연초록</div><div class="ai-bubble">{msg["content"]}</div></div></div>''', unsafe_allow_html=True)

if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("생각 중..."):
        try:
            res = model.generate_content(prompt)
            answer = res.text
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
        except Exception as e:
            st.error(f"오류: {e}")

if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    speak(st.session_state.messages[-1]["content"])


