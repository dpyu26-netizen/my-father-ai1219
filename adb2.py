import streamlit as st
import google.generativeai as genai
import requests
import base64
from datetime import datetime

# --- 1. 보안 설정 (키 숨기기) ---
# 세션 상태에 키가 없으면 입력을 받습니다.
if "GEMINI_API_KEY" not in st.session_state:
    st.session_state.GEMINI_API_KEY = ""
if "ELEVENLABS_API_KEY" not in st.session_state:
    st.session_state.ELEVENLABS_API_KEY = ""

# 사이드바에 키 입력창 배치
with st.sidebar:
    st.header("🔑 API 설정")
    g_key = st.text_input("Gemini API Key", value=st.session_state.GEMINI_API_KEY, type="password")
    e_key = st.text_input("ElevenLabs API Key", value=st.session_state.ELEVENLABS_API_KEY, type="password")
    
    if st.button("설정 저장"):
        st.session_state.GEMINI_API_KEY = g_key
        st.session_state.ELEVENLABS_API_KEY = e_key
        st.success("키가 설정되었습니다!")

# 키가 설정되었을 때만 모델 초기화
if st.session_state.GEMINI_API_KEY:
    genai.configure(api_key=st.session_state.GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash') # 최신 모델명 확인
else:
    st.warning("왼쪽 사이드바에서 Gemini API 키를 입력해주세요.")
    st.stop()

# 보이스 ID 및 웹후크는 그대로 유지 (공개되어도 비교적 안전한 정보들)
VOICE_ID = "dHC7jAYDvo5m8CkyQZnL"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1461850433458016308/6olE8TMTSyKgM81_p5BdA8ZtrnL1uo5NyD1Y7Yt8F-taUM_v1KfnRUCNV4FoiCRerBYQ"

# --- 2. 디자인 및 화면 설정 ---
st.set_page_config(page_title="AI 초록", page_icon="🟢")

st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .user-bubble { background-color: #fee500; padding: 12px; border-radius: 15px; margin-bottom: 10px; display: inline-block; float: right; clear: both; color: black; font-family: 'Malgun Gothic'; }
    .ai-container { display: flex; align-items: flex-start; margin-bottom: 10px; clear: both; }
    .profile-img { width: 45px; height: 45px; border-radius: 50%; margin-right: 10px; }
    .ai-bubble { background-color: white; padding: 12px; border-radius: 15px; display: inline-block; color: black; border: 1px solid #ddd; }
    .ai-name { font-size: 13px; color: #555; margin-bottom: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. 핵심 기능 함수 ---
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

# --- 4. 메인 채팅 ---
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
    
    with st.spinner("연초록이 대답을 적는 중..."):
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
