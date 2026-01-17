import streamlit as st
import google.generativeai as genai
import requests
import base64
from datetime import datetime
import os
import json

# --- 1. API 키 저장/불러오기 함수 ---
KEY_FILE = "keys.json"
ADMIN_PASSWORD = "1234" # 여기에 관리자용 비밀번호를 정하세요!

def save_keys(g_key, e_key):
    with open(KEY_FILE, "w") as f:
        json.dump({"gemini": g_key, "eleven": e_key}, f)

def load_keys():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            return json.load(f)
    return None

# 키 로드 시도
saved_data = load_keys()
GEMINI_API_KEY = saved_data["gemini"] if saved_data else ""
ELEVENLABS_API_KEY = saved_data["eleven"] if saved_data else ""

# --- 2. 사이드바: 관리자 로그인 및 키 등록 ---
with st.sidebar:
    st.header("⚙️ 관리자 설정")
    admin_pw = st.text_input("관리자 비밀번호", type="password")
    
    if admin_pw == ADMIN_PASSWORD:
        st.success("인증되었습니다!")
        new_g_key = st.text_input("Gemini API 키", value=GEMINI_API_KEY)
        new_e_key = st.text_input("ElevenLabs API 키", value=ELEVENLABS_API_KEY)
        if st.button("서버에 키 저장 (모든 사용자 적용)"):
            save_keys(new_g_key, new_e_key)
            st.rerun()
    else:
        st.info("비밀번호를 입력하면 API를 설정할 수 있습니다.")

# API 초기화 (저장된 키가 있을 때만)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("서버에 등록된 API 키가 없습니다. 관리자에게 문의하세요.")
    st.stop()

# --- 3. 디자인 및 나머지 로직 (기존과 동일) ---
VOICE_ID = "dHC7jAYDvo5m8CkyQZnL"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1461850433458016308/6olE8TMTSyKgM81_p5BdA8ZtrnL1uo5NyD1Y7Yt8F-taUM_v1KfnRUCNV4FoiCRerBYQ"

st.set_page_config(page_title="AI 비서 초록", page_icon="🟢")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .user-bubble { background-color: #fee500; padding: 12px; border-radius: 15px; margin-bottom: 10px; display: inline-block; float: right; clear: both; color: #000000 !important; font-family: 'Malgun Gothic'; }
    .ai-container { display: flex; align-items: flex-start; margin-bottom: 10px; clear: both; }
    .profile-img { width: 45px; height: 45px; border-radius: 50%; margin-right: 10px; border: 2px solid #2e7d32; object-fit: cover; }
    .ai-bubble { background-color: #262730; padding: 12px; border-radius: 15px; display: inline-block; color: #ffffff !important; border: 1px solid #444; }
    .ai-name { font-size: 13px; color: #a0a0a0 !important; margin-bottom: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 프로필 사진 처리
if os.path.exists("profile.jpg"):
    with open("profile.jpg", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
        PROFILE_IMG_HTML = f'data:image/jpg;base64,{img_b64}'
else:
    PROFILE_IMG_HTML = "https://cdn-icons-png.flaticon.com/512/4333/4333609.png"

# 대화 내용 세션
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기능 함수들 (디스코드, 음성)
def send_to_discord(u, a):
    requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [{"title": "🟢 로그", "fields": [{"name": "👤 유저", "value": u}, {"name": "🤖 초록", "value": a}]}]})

def speak(text):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        res = requests.post(url, json={"text": text, "model_id": "eleven_multilingual_v2"}, headers={"xi-api-key": ELEVENLABS_API_KEY})
        if res.status_code == 200:
            b64 = base64.b64encode(res.content).decode()
            st.markdown(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
    except: pass

# 채팅 화면 구현
st.title("🎙️ AI 비서 '초록'")

for msg in st.session_state.messages:
    role_class = "user-bubble" if msg["role"] == "user" else "ai-bubble"
    if msg["role"] == "user":
        st.markdown(f'<div class="{role_class}">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'''<div class="ai-container"><img src="{PROFILE_IMG_HTML}" class="profile-img"><div><div class="ai-name">연초록</div><div class="{role_class}">{msg["content"]}</div></div></div>''', unsafe_allow_html=True)

if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("초록이가 생각 중..."):
        try:
            res = model.generate_content(prompt)
            answer = res.text
            st.session_state.messages.append({"role": "assistant", "content": answer})
            send_to_discord(prompt, answer)
            st.rerun()
        except Exception as e:
            st.error(f"오류: {e}")

if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    speak(st.session_state.messages[-1]["content"])
