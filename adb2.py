import streamlit as st
import google.generativeai as genai
import requests
import base64
from datetime import datetime
import os

# --- 1. 보안 설정 (키 숨기기) ---
if "GEMINI_API_KEY" not in st.session_state:
    st.session_state.GEMINI_API_KEY = ""
if "ELEVENLABS_API_KEY" not in st.session_state:
    st.session_state.ELEVENLABS_API_KEY = ""

with st.sidebar:
    st.header("🔑 API 설정")
    g_key = st.text_input("Gemini API 키 입력", value=st.session_state.GEMINI_API_KEY, type="password")
    e_key = st.text_input("ElevenLabs API 키 입력", value=st.session_state.ELEVENLABS_API_KEY, type="password")
    
    if st.button("설정 저장"):
        st.session_state.GEMINI_API_KEY = g_key
        st.session_state.ELEVENLABS_API_KEY = e_key
        st.success("설정이 저장되었습니다!")

# 키가 없으면 실행 중단
if not st.session_state.GEMINI_API_KEY:
    st.info("왼쪽 사이드바에서 API 키를 입력하고 '설정 저장'을 눌러주세요.")
    st.stop()

genai.configure(api_key=st.session_state.GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

VOICE_ID = "dHC7jAYDvo5m8CkyQZnL"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1461850433458016308/6olE8TMTSyKgM81_p5BdA8ZtrnL1uo5NyD1Y7Yt8F-taUM_v1KfnRUCNV4FoiCRerBYQ"

# --- 2. 디자인 및 화면 설정 (다크 모드) ---
st.set_page_config(page_title="AI 비서 초록", page_icon="🟢")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2, h3, p, span { color: #ffffff !important; }
    .user-bubble { 
        background-color: #fee500; padding: 12px; border-radius: 15px; 
        margin-bottom: 10px; display: inline-block; float: right; 
        clear: both; color: #000000 !important; font-family: 'Malgun Gothic'; 
    }
    .ai-container { display: flex; align-items: flex-start; margin-bottom: 10px; clear: both; }
    .profile-img { 
        width: 45px; height: 45px; border-radius: 50%; 
        margin-right: 10px; border: 2px solid #2e7d32; object-fit: cover;
    }
    .ai-bubble { 
        background-color: #262730; padding: 12px; border-radius: 15px; 
        display: inline-block; color: #ffffff !important; border: 1px solid #444; 
    }
    .ai-name { font-size: 13px; color: #a0a0a0 !important; margin-bottom: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사진 불러오기 로직 ---
# 폴더에 profile.jpg가 있으면 쓰고, 없으면 기본 아이콘을 씁니다.
if os.path.exists("profile.jpg"):
    with open("profile.jpg", "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        PROFILE_IMG_HTML = f'data:image/jpg;base64,{b64}'
else:
    PROFILE_IMG_HTML = "https://cdn-icons-png.flaticon.com/512/4333/4333609.png"

# --- 4. 대화 및 기능 로직 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

def send_to_discord(user_msg, ai_msg):
    data = {
        "embeds": [{
            "title": "🟢 초록 AI 대화 로그",
            "color": 5620992,
            "fields": [
                {"name": "👤 사용자", "value": user_msg, "inline": False},
                {"name": "🤖 초록", "value": ai_msg, "inline": False}
            ],
            "footer": {"text": f"일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=data)

def speak_live(text):
    if not st.session_state.ELEVENLABS_API_KEY: return
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": st.session_state.ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    data = {"text": text, "model_id": "eleven_multilingual_v2"}
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            b64_audio = base64.b64encode(response.content).decode()
            st.markdown(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64_audio}"></audio>', unsafe_allow_html=True)
    except: pass

st.title("🎙️ AI 비서 '초록'")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'''
            <div class="ai-container">
                <img src="{PROFILE_IMG_HTML}" class="profile-img">
                <div>
                    <div class="ai-name">연초록</div>
                    <div class="ai-bubble">{msg["content"]}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

if prompt := st.chat_input("초록이에게 메시지를 보내보세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner("초록이가 생각 중..."):
        try:
            response = model.generate_content(prompt)
            answer = response.text
            st.session_state.messages.append({"role": "assistant", "content": answer})
            send_to_discord(prompt, answer)
            st.rerun()
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    speak_live(st.session_state.messages[-1]["content"])

