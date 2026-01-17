import streamlit as st
import google.generativeai as genai
import requests
import base64
from datetime import datetime
import os

# --- 1. 보안 및 초기 설정 ---
if "GEMINI_API_KEY" not in st.session_state:
    st.session_state.GEMINI_API_KEY = ""
if "ELEVENLABS_API_KEY" not in st.session_state:
    st.session_state.ELEVENLABS_API_KEY = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정 및 관리")
    
    # API 키 입력 섹션
    with st.expander("🔑 API 키 설정"):
        g_key = st.text_input("Gemini API 키", value=st.session_state.GEMINI_API_KEY, type="password")
        e_key = st.text_input("ElevenLabs API 키", value=st.session_state.ELEVENLABS_API_KEY, type="password")
        if st.button("설정 저장"):
            st.session_state.GEMINI_API_KEY = g_key
            st.session_state.ELEVENLABS_API_KEY = e_key
            st.success("저장 완료!")

    st.divider()

    # 채팅 관리 섹션 (삭제, 다운로드)
    st.subheader("💬 채팅 관리")
    
    if st.button("🗑️ 전체 대화 삭제"):
        st.session_state.messages = []
        st.rerun()

    # 대화 내용 텍스트 추출
    chat_text = "\n".join([f"[{m['role'].upper()}] {m['content']}" for m in st.session_state.messages])
    
    st.download_button(
        label="💾 대화 내용 다운로드",
        data=chat_text,
        file_name=f"초록_대화기록_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )

# 키 체크
if not st.session_state.GEMINI_API_KEY:
    st.info("왼쪽 사이드바에서 API 키를 입력해주세요.")
    st.stop()

genai.configure(api_key=st.session_state.GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

VOICE_ID = "dHC7jAYDvo5m8CkyQZnL"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1461850433458016308/6olE8TMTSyKgM81_p5BdA8ZtrnL1uo5NyD1Y7Yt8F-taUM_v1KfnRUCNV4FoiCRerBYQ"

# --- 2. 디자인 (다크 모드 및 말풍선) ---
st.set_page_config(page_title="AI 비서 초록", page_icon="🟢")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
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

# --- 3. 프로필 이미지 처리 ---
# 로컬/GitHub에 있는 profile.jpg 읽기
if os.path.exists("profile.jpg"):
    with open("profile.jpg", "rb") as f:
        img_data = f.read()
        img_b64 = base64.b64encode(img_data).decode()
        PROFILE_IMG_HTML = f'data:image/jpg;base64,{img_b64}'
else:
    # 파일이 없을 때 보여줄 기본 이미지
    PROFILE_IMG_HTML = "https://cdn-icons-png.flaticon.com/512/4333/4333609.png"

# --- 4. 메인 채팅 로직 ---
st.title("🎙️ AI 비서 '초록'")

def send_to_discord(u, a):
    requests.post(DISCORD_WEBHOOK_URL, json={
        "embeds": [{"title": "🟢 대화 로그", "fields": [{"name": "👤 유저", "value": u}, {"name": "🤖 초록", "value": a}]}]
    })

def speak(text):
    if not st.session_state.ELEVENLABS_API_KEY: return
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        res = requests.post(url, json={"text": text, "model_id": "eleven_multilingual_v2"}, headers={"xi-api-key": st.session_state.ELEVENLABS_API_KEY})
        if res.status_code == 200:
            b64 = base64.b64encode(res.content).decode()
            st.markdown(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
    except: pass

# 대화 기록 렌더링
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

if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("생각 중..."):
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
