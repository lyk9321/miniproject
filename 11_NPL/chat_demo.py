# ============================================================
# AI 이모티콘봇 - 카카오 스타일 채팅 데모 (GitHub Models 버전)
# Gemini → GitHub Models API로 변경 (안정적!)
# 실행: streamlit run chat_demo.py
# pip install streamlit openai pillow
# ============================================================

import streamlit as st
from openai import OpenAI
from PIL import Image
from datetime import datetime
import io
import base64

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="AI 이모티콘봇",
    page_icon="💬",
    layout="centered"
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    .stApp { background-color: #b2c7da; }
    .chat-header {
        background: #f9e000; padding: 14px 20px;
        border-radius: 12px 12px 0 0;
        display: flex; align-items: center; gap: 10px;
    }
    .chat-header-name { font-size: 18px; font-weight: 600; color: #222; }
    .bubble-me {
        background: #f9e000; border-radius: 16px 4px 16px 16px;
        padding: 9px 14px; display: inline-block; max-width: 240px;
        font-size: 14px; color: #222; line-height: 1.5; word-break: keep-all;
    }
    .bubble-other {
        background: #fff; border-radius: 4px 16px 16px 16px;
        padding: 9px 14px; display: inline-block; max-width: 240px;
        font-size: 14px; color: #222; line-height: 1.5; word-break: keep-all;
    }
    .chat-time { font-size: 11px; color: rgba(0,0,0,0.45); margin: 2px 4px; }
    .date-divider {
        text-align: center; font-size: 12px; color: #fff;
        background: rgba(0,0,0,0.2); border-radius: 10px;
        padding: 3px 12px; display: inline-block; margin: 8px auto;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 세션 상태 초기화
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = """너는 사용자의 친한 친구처럼 자연스럽게 대화하는 챗봇이다.

[기본 역할]
- 친한 친구처럼 편하고 자연스럽게 반말로 대화한다.
- 실제 카톡 대화처럼 짧고 간결하게 답한다.
- 사용자의 말, 사진, 이모티콘, 짧은 감탄사만으로도 맥락을 이해하고 이어서 대화한다.
- AI처럼 설명하지 말고, 사람처럼 바로 반응한다.

[대화 스타일]
- 기본적으로 1~2문장으로 답한다.
- 문장은 짧고 자연스럽게 끊는다.
- 필요할 때만 ㅋㅋ, ㅎㅎ, ㅠㅠ 같은 표현을 자연스럽게 사용한다.
- 상대방의 감정이나 상황에 먼저 반응한 뒤, 이어서 대화한다.
- 과한 리액션, 오글거리는 말투, 매번 질문하는 방식은 피한다.
- 같은 말투나 표현을 반복하지 않는다.
- 답변은 가볍고 대화체로, 메신저에서 실제 친구가 보낼 법하게 작성한다.
- 지나치게 배려하는 말투, 과한 위로, 과장된 칭찬은 피하고 담백하게 반응한다.

[입력 해석 방식]
- 텍스트가 오면: 내용 + 감정 + 숨은 의도를 함께 파악한다.
- 사진이 오면: 사진에서 보이는 핵심 요소(사람, 사물, 장소, 분위기, 상황)를 먼저 이해하고 자연스럽게 반응한다.
- 이모티콘이나 짧은 표현만 오면: 감정 표현으로 이해하고 그에 맞게 반응한다.
- 텍스트와 사진이 함께 오면: 텍스트의 의미를 우선으로 보고, 사진은 맥락 보조로 활용한다.
- 의미가 불분명하면 단정하지 말고 가볍게 되묻는다.

[사진/이미지 대응 규칙]
- 사진에 대해 답할 때는 먼저 눈에 보이는 내용에 반응한다.
- 분위기, 감정, 상황도 자연스럽게 읽되 과도한 추측은 하지 않는다.
- 사용자가 사진에 대한 평가를 원하지 않았으면 장황한 설명이나 분석을 하지 않는다.
- 예쁘다, 맛있어 보인다, 웃기다, 피곤해 보인다 등 일상적인 반응을 우선한다.

[이모티콘 대응 규칙]
- 이모티콘만 보내도 어색하게 끊지 말고 감정 흐름에 맞춰 답한다.
- 웃음/당황/슬픔/민망함/축하 등으로 자연스럽게 해석한다.
- 예:
  - ㅋㅋㅋ → 같이 웃거나 장난스럽게 받기
  - ㅠㅠ / 😭 → 위로하거나 이유 가볍게 묻기
  - 😍 / 🥹 → 공감하거나 같이 좋아해주기
  - 😑 / … → 분위기 읽고 조심스럽게 반응하기

[응답 원칙]
- 먼저 공감하거나 상황을 받는다.
- 그 다음 짧게 이어서 말한다.
- 필요할 때만 짧게 질문한다.
- 사용자가 진지하면 같이 진지하게, 장난치면 가볍게 맞춰준다.
- 사용자의 말투가 바뀌면 그 톤에 맞춰 자연스럽게 조절한다.
- 대화를 이어가되, 억지로 화제를 늘리지는 않는다.
- 직전 답변과 비슷한 표현, 종결어미, 감탄사를 반복하지 않는다.

[절대 하지 말 것]
- 존댓말 사용
- 3문장 이상 길게 답하기
- AI, 챗봇, 시스템, 모델 같은 표현
- 상담사처럼 말하기
- 매번 똑같은 공감 표현 쓰기
- 보이지 않는 내용을 확신해서 말하기
- 지나치게 교과서식으로 설명하기

[대화 예시]

사용자: 오늘 진짜 개피곤함
답변: 헐 오늘 많이 빡셌나보다 ㅠㅠ

사용자: 😭
답변: 왜 ㅠㅠ 무슨 일인데

사용자: 사진 전송(카페 디저트 사진)
답변: 와 이거 뭐야 맛있겠다 ㅋㅋ

사용자: 사진 전송(흐린 하늘, 퇴근길)
답변: 오늘 분위기 왜 이렇게 축 처지냐 ㅠㅠ 퇴근길이야?

사용자: 알겠어
답변: 오케이 ㅋㅋ

[출력 목표]
항상 '실제로 친한 친구가 카톡으로 보낼 법한 답장'처럼 답한다."""

if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "show_emoticon_panel" not in st.session_state:
    st.session_state.show_emoticon_panel = False
if "emoticon_images" not in st.session_state:
    st.session_state.emoticon_images = {}

# ============================================================
# 유틸 함수
# ============================================================
def get_time():
    now = datetime.now()
    h   = now.hour % 12 or 12
    m   = now.strftime("%M")
    ap  = "오후" if now.hour >= 12 else "오전"
    return f"{ap} {h}:{m}"

def get_date():
    now      = datetime.now()
    weekdays = ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"]
    return f"{now.year}년 {now.month}월 {now.day}일 {weekdays[now.weekday()]}"

def img_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def describe_emoticon_with_vision(img: Image.Image, api_key: str) -> str:
    """
    GPT-4o-mini vision으로 이모티콘 이미지를 분석해서
    감정/상황을 텍스트로 변환
    GitHub Models도 vision 지원!
    """
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=api_key
    )
    b64 = img_to_b64(img)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "이 이모티콘의 감정과 상황을 한 문장으로 짧게 설명해줘. 예: '기쁘고 신나는 표정', '슬프고 우는 표정'"
                        }
                    ]
                }
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except:
        return "이모티콘"

# ============================================================
# GitHub Models API로 채팅
# ============================================================
def send_message(user_content: str, is_emoticon: bool = False):
    """
    GitHub Models (gpt-4o-mini)로 메시지 전송
    - 텍스트: 그대로 전달
    - 이모티콘: vision으로 분석한 설명을 텍스트로 전달
    """
    if not st.session_state.api_key:
        return "API 키를 왼쪽 사이드바에 입력해줘! 🔑"

    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=st.session_state.api_key
    )

    # 시스템 프롬프트 + 이전 대화 기록 구성
    messages = [{"role": "system", "content": st.session_state.system_prompt}]

    for msg in st.session_state.messages:
        if msg["type"] == "text":
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        elif msg["type"] == "image" and msg["role"] == "user":
            # 이모티콘은 설명 텍스트로 기록에 포함
            desc = msg.get("description", "이모티콘")
            messages.append({"role": "user", "content": f"(이모티콘 전송: {desc})"})

    # 새 메시지 추가
    messages.append({"role": "user", "content": user_content})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=100,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"오류 발생: {str(e)}"

# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ API 키 설정")
    api_key_input = st.text_input(
        "GitHub 토큰 (ghp_...)",
        type="password",
        placeholder="ghp_xxxxxxxxxxxx",
        value=st.session_state.api_key
    )
    if st.button("API 키 저장", use_container_width=True):
        st.session_state.api_key  = api_key_input
        st.session_state.messages = []
        st.success("저장됨!")

    st.divider()

    st.markdown("### 💬 시스템 프롬프트")
    new_prompt = st.text_area(
        "프롬프트",
        value=st.session_state.system_prompt,
        height=250,
        label_visibility="collapsed"
    )
    if st.button("프롬프트 적용", use_container_width=True):
        st.session_state.system_prompt = new_prompt
        st.session_state.messages      = []
        st.success("적용됨! 대화가 초기화됐어.")

    st.divider()

    st.markdown("### 🎭 이모티콘 등록")
    st.caption("만든 이모티콘 PNG 파일을 올려줘! GPT가 이미지를 보고 알아서 반응해.")
    uploaded_emoticons = st.file_uploader(
        "이모티콘 업로드",
        type=["png","jpg","jpeg"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if uploaded_emoticons:
        for f in uploaded_emoticons:
            st.session_state.emoticon_images[f.name] = Image.open(f).convert("RGBA")
        st.success(f"{len(st.session_state.emoticon_images)}개 등록됨!")

    if st.session_state.emoticon_images:
        st.markdown("**등록된 이모티콘:**")
        pcols = st.columns(3)
        for i, (name, img) in enumerate(st.session_state.emoticon_images.items()):
            with pcols[i % 3]:
                st.image(img, caption=name[:8], use_container_width=True)

    st.divider()
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ============================================================
# 채팅 UI
# ============================================================
st.markdown("""
<div class="chat-header">
    <span style="font-size:24px;">🤖</span>
    <span class="chat-header-name">AI 이모티콘봇</span>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1,2,1])
with c2:
    st.markdown(
        f'<div class="date-divider">{get_date()}</div>',
        unsafe_allow_html=True
    )

# 메시지 출력
for msg in st.session_state.messages:
    if msg["role"] == "user":
        col1, col2 = st.columns([1, 2])
        with col2:
            if msg["type"] == "text":
                st.markdown(
                    f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;">'
                    f'<div class="bubble-me">{msg["content"]}</div>'
                    f'<span class="chat-time">{msg.get("time","")}</span></div>',
                    unsafe_allow_html=True
                )
            elif msg["type"] == "image":
                b64 = img_to_b64(msg["image"])
                st.markdown(
                    f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;">'
                    f'<img src="data:image/png;base64,{b64}" '
                    f'style="width:130px;border-radius:12px;background:#f9e000;padding:6px;">'
                    f'<span class="chat-time">{msg.get("time","")}</span></div>',
                    unsafe_allow_html=True
                )
    else:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(
                f'<div style="display:flex;align-items:flex-end;gap:6px;">'
                f'<div style="font-size:28px;">🤖</div>'
                f'<div style="display:flex;flex-direction:column;gap:2px;">'
                f'<span style="font-size:12px;color:#fff;">AI 이모티콘봇</span>'
                f'<div class="bubble-other">{msg["content"]}</div>'
                f'<span class="chat-time">{msg.get("time","")}</span>'
                f'</div></div>',
                unsafe_allow_html=True
            )

# 이모티콘 패널
if st.session_state.show_emoticon_panel:
    if st.session_state.emoticon_images:
        st.markdown("---")
        st.markdown("**이모티콘 선택**")
        em_cols = st.columns(4)
        for i, (name, img) in enumerate(st.session_state.emoticon_images.items()):
            with em_cols[i % 4]:
                st.image(img, use_container_width=True)
                if st.button("전송", key=f"send_em_{name}"):
                    now = get_time()
                    st.session_state.show_emoticon_panel = False

                    # vision으로 이모티콘 내용 분석
                    with st.spinner("이모티콘 분석 중..."):
                        desc = describe_emoticon_with_vision(
                            img, st.session_state.api_key
                        )

                    # 이모티콘 메시지 저장
                    st.session_state.messages.append({
                        "role":        "user",
                        "type":        "image",
                        "image":       img,
                        "description": desc,
                        "time":        now
                    })

                    # AI 응답
                    with st.spinner(""):
                        reply = send_message(
                            f"친구가 '{desc}' 이모티콘을 보냈어. "
                            f"자연스럽게 짧게 반응해줘."
                        )
                    st.session_state.messages.append({
                        "role":    "assistant",
                        "type":    "text",
                        "content": reply,
                        "time":    now
                    })
                    st.rerun()
    else:
        st.warning("사이드바에서 이모티콘을 먼저 등록해줘!")

# 입력창
st.markdown("---")
btn_col, input_col = st.columns([1, 8])
with btn_col:
    if st.button("😊", help="이모티콘 보내기", use_container_width=True):
        st.session_state.show_emoticon_panel = not st.session_state.show_emoticon_panel
        st.rerun()
with input_col:
    user_input = st.chat_input("메시지 입력")

# 텍스트 전송
if user_input:
    now = get_time()
    st.session_state.messages.append({
        "role": "user", "type": "text",
        "content": user_input, "time": now
    })
    with st.spinner(""):
        reply = send_message(user_input)
    st.session_state.messages.append({
        "role": "assistant", "type": "text",
        "content": reply, "time": now
    })
    st.rerun()
