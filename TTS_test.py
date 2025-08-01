import streamlit as st
import openai
import streamlit.components.v1 as components
import re
import requests

# 페이지 설정
st.set_page_config(page_title="치치와 감정 알아보기", page_icon="🐱")
st.title("🐱 치치에게 한 번 물어보라옹!")
st.write("무슨 일이 있었냥? 어떤 마음인지 함께 알아보자옹!")

# ✅ secrets에서 API 키 가져오기
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 세션 상태 초기화
if "stage" not in st.session_state:
    st.session_state.stage = "ask_who"
if "who" not in st.session_state:
    st.session_state.who = ""
if "when" not in st.session_state:
    st.session_state.when = ""
if "what" not in st.session_state:
    st.session_state.what = ""
if "emotion_choices" not in st.session_state:
    st.session_state.emotion_choices = []
if "previous_choices" not in st.session_state:
    st.session_state.previous_choices = []
if "final_emotion" not in st.session_state:
    st.session_state.final_emotion = ""
if "response" not in st.session_state:
    st.session_state.response = ""

# 이모지 제거 함수 (TTS용)
def remove_emojis(text):
    return re.sub(r'[^\w\s.,!?가-힣ㄱ-ㅎㅏ-ㅣ]', '', text)

# CLOVA TTS 함수
def clova_tts(text, speaker="taeo"):
    CLOVA_API_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": st.secrets["NCLOUD_CLIENT_ID"],
        "X-NCP-APIGW-API-KEY": st.secrets["NCLOUD_CLIENT_SECRET"]
    }
    cleaned_text = remove_emojis(text)
    data = {
        "speaker": speaker,
        "volume": "0",
        "speed": "0",
        "pitch": "0",
        "format": "mp3",
        "text": cleaned_text
    }
    response = requests.post(CLOVA_API_URL, headers=headers, data=data)
    if response.status_code == 200:
        return response.content
    else:
        st.error(f"❌ 음성 합성 실패: {response.status_code} - {response.text}")
        return None

# GPT 응답 생성 함수
def get_emotion_candidates(who, when, what):
    prompt = f"누구: {who}\n언제: {when}\n어떤 일: {what}\n위 상황에서 예상되는 감정 단어 3개와 각 단어의 정의를 다음 형식으로 알려줘: 감정단어: 정의. 설명이나 인사말 없이 감정 단어와 정의만 나열해줘."
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "넌 감정을 분석해주는 따뜻한 고양이 치치야. 사용자에게 '~냥' 또는 '~옹'으로 문장이 끝나는 말투로 따뜻하고 사랑스럽게 반응하고, 상황을 듣고 예상 감정 단어를 정의와 함께 제공해줘."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def get_alternative_emotions(who, when, what):
    prompt = f"누구: {who}\n언제: {when}\n어떤 일: {what}\n이전에 제공한 감정이 아니라고 했을 때, 대체 가능한 새로우면서 앞서 제시한 단어와 다른 감정 단어 3개와 그 정의를 감정단어: 정의 형태로 알려줘. 감정 외의 문장은 포함하지 말고 감정 단어만 제시해줘."
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "넌 감정을 분석해주는 따뜻한 고양이 치치야. 사용자에게 '~냥' 또는 '~옹'으로 문장이 끝나는 말투로 따뜻하고 사랑스럽게 반응하고, 상황을 듣고 예상 감정 단어를 정의와 함께 제공해줘."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def get_final_response(emotion, who, when, what):
    prompt = f"상황: 누구={who}, 언제={when}, 어떤일={what}\n감정: {emotion}\n초등학생처럼 단어는 쉽고 말투는 따뜻하게, '~냥' 또는 '~옹' 어미를 섞어 고양이 치치가 말하듯 공감, 위로, 격려, 칭찬 중 하나를 골라 반응해줘. 이모지 한 개도 포함해줘. 반드시 학생이 사용한 인물의 명칭을 그대로 사용하고, 학생이 서술한 상황과 그에 대해 선택한 감정단어를 사용해서 상황에 어울리는 위로나 공감을 해야해. 말의 끝은 '~옹', '~냥'으로 끝나지만 맞춤법은 지켜줘."
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "넌 고양이 치치야. '~냥' 또는 '~옹' 말투로 귀엽고 다정하게 위로하고 감정을 받아주는 역할이야."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# 단계별 인터페이스
if st.session_state.stage == "ask_who":
    st.session_state.who = st.text_input("🐱 누구와 있었던 일이냐옹?")
    if st.button("다음") and st.session_state.who.strip():
        st.session_state.stage = "ask_when"
        st.rerun()

elif st.session_state.stage == "ask_when":
    st.session_state.when = st.text_input("🐱 그건 언제 있었던 일이냥?")
    if st.button("다음") and st.session_state.when.strip():
        st.session_state.stage = "ask_what"
        st.rerun()

elif st.session_state.stage == "ask_what":
    st.session_state.what = st.text_area("🐱 어떤 일이 있었는지 자세히 말해주라옹")
    if st.button("다음") and st.session_state.what.strip():
        with st.spinner("치치가 감정을 추측 중이다옹... 🐾"):
            result = get_emotion_candidates(st.session_state.who, st.session_state.when, st.session_state.what)
            st.session_state.emotion_choices = result.split("\n")
            st.session_state.previous_choices = st.session_state.emotion_choices.copy()
        st.session_state.stage = "choose_emotion"
        st.rerun()

elif st.session_state.stage == "choose_emotion":
    st.write("🐱 치치의 생각은 이렇다옹:")
    emotion_only = [e for e in st.session_state.emotion_choices if ":" in e and not any(x in e for x in ["생각", "이럴", "이런 경우"])]
    chosen = st.radio("이 중 어떤 감정이 제일 비슷하냥?", options=emotion_only + ["이 감정들이 아니야"])

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("선택"):
            if chosen == "이 감정들이 아니야":
                with st.spinner("다른 감정을 찾아보는 중이냥..."):
                    new_choices = get_alternative_emotions(st.session_state.who, st.session_state.when, st.session_state.what)
                    st.session_state.previous_choices = st.session_state.emotion_choices.copy()
                    st.session_state.emotion_choices = new_choices.split("\n")
                    st.session_state.stage = "choose_emotion"
                    st.rerun()
            else:
                st.session_state.final_emotion = chosen.split(":")[0].strip()
                st.session_state.stage = "show_response"
                st.rerun()
    with col2:
        if st.session_state.previous_choices != st.session_state.emotion_choices:
            if st.button("↩️ 이전으로"):
                st.session_state.emotion_choices, st.session_state.previous_choices = st.session_state.previous_choices, st.session_state.emotion_choices
                st.rerun()

elif st.session_state.stage == "show_response":
    st.write("🐱 치치의 대답:")
    if not st.session_state.response:
        st.session_state.response = get_final_response(st.session_state.final_emotion, st.session_state.who, st.session_state.when, st.session_state.what)

    st.success(st.session_state.response)

    speak_col = st.columns([6, 1])[1]
    with speak_col:
        if st.button("▶️", help="버튼을 누르면 치치의 대답을 읽어줘!"):
            audio = clova_tts(st.session_state.response)
            if audio:
                st.audio(audio, format="audio/mp3")

    if st.button("↩️ 다시 시작하기"):
        for key in ["stage", "who", "when", "what", "emotion_choices", "previous_choices", "final_emotion", "response"]:
            st.session_state.pop(key, None)
        st.rerun()
