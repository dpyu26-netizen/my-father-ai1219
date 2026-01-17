import streamlit as st
import google.generativeai as genai
import requests
import base64
from datetime import datetime

# --- 1. 보안 설정 (키 숨기기) ---
if "GEMINI_API_KEY" not in st.session_state:
    st.session_state.GEMINI_API_KEY = ""
if "ELEVENLABS_API_KEY" not in st.session_state:
    st.session_state.ELEVENLABS_API_KEY = ""

with st.sidebar:
    st.header("🔑 API 설정")
    g_key = st.text_input("Gemini API Key", value=st.session_state.GEMINI_API_KEY, type="password")
    e_key = st.text_input("ElevenLabs API Key", value=st.session_state.ELEVENLABS_API_KEY, type="password")
    
    if st.button("설정 저장"):
        st.session_state.GEMINI_API_KEY = g_key
        st.session_state.ELEVENLABS_API_KEY = e_key
        st.success("키가 저장되었습니다!")

# 키 체크 및 모델 설정
if st.session_state.GEMINI_API_KEY:
    genai.configure(api_key=st.session_state.GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.info("왼쪽 사이드바에서 API 키를 먼저 입력해주세요.")
    st.stop()

VOICE_ID = "dHC7jAYDvo5m8CkyQZnL"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1461850433458016308/6olE8TMTSyKgM81_p5BdA8ZtrnL1uo5NyD1Y7Yt8F-taUM_v1KfnRUCNV4FoiCRerBYQ"

# --- 2. 다크 모드 디자인 설정 ---
st.set_page_config(page_title="AI 초록 - Dark", page_icon="🟢")

st.markdown("""
    <style>
    /* 전체 배경을 검은색으로 */
    .stApp { 
        background-color: #0e1117; 
        color: #ffffff;
    }
    
    /* 제목 및 텍스트 색상 화이트로 고정 */
    h1, h2, h3, p, span {
        color: #ffffff !important;
    }

    /* 유저 말풍선 (카톡 노란색 유지하되 가독성 높임) */
    .user-bubble { 
        background-color: #fee500; 
        padding: 12px; 
        border-radius: 15px; 
        margin-bottom: 10px; 
        display: inline-block; 
        float: right; 
        clear: both; 
        color: #000000 !important; /* 글자는 검은색 */
        font-family: 'Malgun Gothic';
        font-weight: 500;
    }

    /* AI 말풍선 (어두운 배경에 맞는 진한 회색) */
    .ai-container { display: flex; align-items: flex-start; margin-bottom: 10px; clear: both; }
    .profile-img { width: 45px; height: 45px; border-radius: 50%; margin-right: 10px; border: 2px solid #2e7d32; }
    
    .ai-bubble { 
        background-color: #262730; 
        padding: 12px; 
        border-radius: 15px; 
        display: inline-block; 
        color: #ffffff !important; 
        border: 1px solid #444;
    }
    
    .ai-name { 
        font-size: 13px; 
        color: #a0a0a0 !important; 
        margin-bottom: 5px; 
        font-weight: bold; 
    }

    /* 하단 입력창 배경 조정 */
    .stChatInputContainer {
        background-color: #1a1c24 !important;
    }
    </style>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. 기능 함수 ---
def send_to_discord(user_msg, ai_msg):
    data = {
        "embeds": [{
            "title": "🟢 초록 AI 대화 로그",
            "color": 5620992,
            "fields": [
                {"name": "👤 사용자", "value": user_msg, "inline": False},
                {"name": "🤖 초록", "value": ai_msg, "inline": False}
            ],
            "footer": {"text": f"발생 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
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
            b64 = base64.b64encode(response.content).decode()
            st.markdown(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
    except: pass

# --- 4. 메인 화면 출력 ---
st.title("🎙️ AI 비서 '초록'")
PROFILE_URL = "https://cdn-icons-png.flaticon.com/512/4333/4333609.png"

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'''
            <div class="ai-container">
                <img src="{PROFILE_URL}" class="profile-img">
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
            response = model.generate_content(prompt)
            answer = response.text
            st.session_state.messages.append({"role": "assistant", "content": answer})
            send_to_discord(prompt, answer)
            st.rerun()
        except Exception as e:
            st.error(f"오류: {e}")

if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    speak_live(st.session_state.messages[-1]["content"])
