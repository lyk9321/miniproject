"""
Tab 1: 경기 & 예측
streamlit run tab1.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from score_calculator import get_recommendation

TEAM_COLORS = {
    "LG":  "#C8102E", "두산": "#131230", "KIA":  "#EA0029",
    "삼성": "#074CA1", "한화": "#FF6200", "롯데": "#E31837",
    "SSG": "#CE0E2D", "NC":  "#071D49",  "KT":  "#000000",
    "키움": "#570514",
}

GAME_TIME = {
    "월": "18:30", "화": "18:30", "수": "18:30",
    "목": "18:30", "금": "18:30",
    "토": "17:00", "일": "14:00",
}

SCORE_EXPLANATIONS = {
    "승률예측": {
        "icon": "⚾", "label": "승률 예측",
        "color": "#1A56DB", "bg": "#EFF6FF", "weight": "35%",
        "method": "로지스틱 회귀 모델",
        "desc": "2016~2025 시즌 약 7,200경기를 학습한 로지스틱 회귀 모델로 계산해요. 홈팀/원정팀의 시즌 승률과 상대전 승률을 피처로 사용하며, 야구의 홈 어드밴티지(홈팀 승률 약 54%)를 반영해요.",
    },
    "최근폼": {
        "icon": "📈", "label": "최근 폼",
        "color": "#059669", "bg": "#ECFDF5", "weight": "25%",
        "method": "이번 시즌 최근 10경기 승률",
        "desc": "이번 시즌에서 가장 최근 10경기의 승률을 기반으로 해요. 현재 팀의 컨디션을 가장 잘 반영하는 지표예요. 시즌 초반(10경기 미만)에는 지난 시즌 기록과 가중 평균으로 보완해요.",
    },
    "상대전": {
        "icon": "🤝", "label": "상대 전적",
        "color": "#7C3AED", "bg": "#F5F3FF", "weight": "20%",
        "method": "이번 시즌 + 최근 3시즌 맞대결 승률",
        "desc": "두 팀이 맞붙었을 때의 역대 상성을 반영해요. 이번 시즌 맞대결이 5경기 이상이면 이번 시즌 기록을 사용하고, 5경기 미만이면 최근 3시즌 통합 상대전 기록으로 대체해요.",
    },
    "원정승률": {
        "icon": "✈️", "label": "원정 승률",
        "color": "#D97706", "bg": "#FFFBEB", "weight": "20%",
        "method": "이번 시즌 전체 원정 경기 승률",
        "desc": "이번 시즌 홈 경기를 제외한 원정 경기만의 승률이에요. 원정 특화 성향을 측정하는 지표로, 원정에서 강한 팀인지 파악해요. 시즌 초반(10경기 미만)에는 지난 시즌과 가중 평균으로 보완해요.",
    },
}

# ── CSS 클래스 전체 정의 ──────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&family=Bebas+Neue&display=swap');

    .stApp { background-color: #F4F6F9; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .block-container { padding-top: 4rem !important; }

    .kbo-section-label {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 11px; font-weight: 700; color: #1A56DB;
        letter-spacing: 2px; text-transform: uppercase;
        margin-bottom: 4px;
    }
    .kbo-section-title {
        font-family: 'Bebas Neue', 'Noto Sans KR', sans-serif;
        font-size: 36px; color: #0D1B2A;
        margin-bottom: 24px; letter-spacing: 1px;
    }

    /* 경기 카드 */
    .kbo-game-card {
        background: linear-gradient(135deg, #0D1B2A 0%, #1A3A5C 100%);
        border-radius: 20px; padding: 28px 32px; color: white;
        box-shadow: 0 8px 32px rgba(13,27,42,0.25);
    }
    .kbo-card-header {
        display: flex; justify-content: space-between;
        align-items: flex-start; margin-bottom: 20px;
    }
    .kbo-date-txt {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 13px; color: rgba(255,255,255,0.6); margin-bottom: 4px;
    }
    .kbo-time-txt {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 13px; color: rgba(255,255,255,0.4);
    }
    .kbo-weather-badge {
        background: rgba(255,255,255,0.12); border-radius: 20px;
        padding: 6px 14px; font-family: 'Noto Sans KR', sans-serif;
        font-size: 12px; color: white; white-space: nowrap;
    }
    .kbo-teams-row {
        display: flex; align-items: center;
        justify-content: center; gap: 32px; margin-bottom: 28px;
    }
    .kbo-team-wrap { text-align: center; }
    .kbo-team-badge {
        width: 64px; height: 64px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Bebas Neue', 'Noto Sans KR', sans-serif; font-size: 18px;
        font-weight: 700; color: white; margin: 0 auto;
        border: 3px solid rgba(255,255,255,0.3);
    }
    .kbo-team-lbl {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 13px; color: rgba(255,255,255,0.85); margin-top: 6px;
    }
    .kbo-team-sub {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 2px;
    }
    .kbo-vs {
        font-family: 'Bebas Neue', 'Noto Sans KR', sans-serif;
        font-size: 28px; color: rgba(255,255,255,0.35);
    }
    .kbo-prob-label {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 11px; color: rgba(255,255,255,0.5);
        letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px;
    }
    .kbo-prob-bar {
        display: flex; height: 8px; border-radius: 4px;
        overflow: hidden; margin-bottom: 6px;
    }
    .kbo-prob-nums {
        display: flex; justify-content: space-between;
    }
    .kbo-prob-my {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 13px; color: white; font-weight: 600;
    }
    .kbo-prob-op {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 13px; color: rgba(255,255,255,0.6);
    }

    /* 추천도 점수 카드 */
    .kbo-score-card {
        background: white; border-radius: 16px; padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #E8ECF0;
    }
    .kbo-score-lbl {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 12px; font-weight: 700; color: #6B7280;
        letter-spacing: 1px; margin-bottom: 8px;
    }
    .kbo-score-num {
        font-family: 'Bebas Neue', 'Noto Sans KR', sans-serif;
        font-size: 56px; line-height: 1;
    }
    .kbo-score-sub {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 13px; color: #9CA3AF; margin-bottom: 8px;
    }
    .kbo-grade-badge {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 13px; font-weight: 700;
        padding: 4px 12px; border-radius: 20px;
        display: inline-block; margin-bottom: 20px;
    }
    .kbo-bar-row {
        display: flex; justify-content: space-between;
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 13px; color: #4B5563; margin-bottom: 4px;
    }
    .kbo-bar-bg {
        background: #F3F4F6; border-radius: 4px;
        height: 8px; margin-bottom: 12px; overflow: hidden;
    }
    .kbo-bar-fill { height: 100%; border-radius: 4px; }

    /* 상세 카드 */
    .kbo-detail-card {
        border-radius: 14px; padding: 24px;
    }
    .kbo-detail-score {
        font-family: 'Bebas Neue', 'Noto Sans KR', sans-serif;
        font-size: 42px; line-height: 1; text-align: center;
    }
    .kbo-detail-lbl {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 12px; color: #6B7280;
        margin-bottom: 4px; text-align: center; padding-top: 4px;
    }
    .kbo-detail-status {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 11px; margin-top: 4px; text-align: center;
    }
    .kbo-detail-section {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 11px; font-weight: 700; color: #374151;
        margin-bottom: 6px; margin-top: 10px;
    }
    .kbo-detail-content {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 11px; color: #6B7280;
        margin-bottom: 14px; line-height: 1.7;
    }

    /* 사이드바 게임 리스트 */
    .kbo-sidebar-badge {
        width: 36px; height: 36px; border-radius: 50%;
        display: inline-flex; align-items: center;
        justify-content: center; font-size: 11px;
        font-weight: 900; color: white; flex-shrink: 0;
    }
    .kbo-sidebar-item {
        background: white; border-radius: 12px;
        padding: 12px 14px; margin-bottom: 8px;
        border: 1px solid #F3F4F6;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        font-family: 'Noto Sans KR', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# ── 데이터 로드 ───────────────────────────────────────────────────────
@st.cache_data
def load_schedule():
    df = pd.read_csv("kbo_schedule.csv", encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"])
    return df

@st.cache_data
def load_results():
    df = pd.read_csv("kbo_results_all.csv", encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"])
    return df

def get_away_win_rates(results, city):
    city_home = {
        "서울": ["LG","두산","키움"], "인천": ["SSG"],
        "수원": ["KT"], "대전": ["한화"], "대구": ["삼성"],
        "광주": ["KIA"], "부산": ["롯데"], "창원": ["NC"],
    }
    home_teams = city_home.get(city, [])
    if not home_teams:
        return pd.DataFrame()
    recent  = results["시즌"].max()
    seasons = list(range(recent - 4, recent + 1))
    city_g  = results[results["시즌"].isin(seasons) & results["홈팀"].isin(home_teams)]
    rows = []
    for team in TEAM_COLORS:
        g = city_g[city_g["원정팀"] == team]
        if len(g) == 0: continue
        rows.append({"팀": team, "원정승률": g["원정팀승리"].mean(), "경기수": len(g)})
    return pd.DataFrame(rows).sort_values("원정승률", ascending=False).head(5)

# ── 경기 카드 ─────────────────────────────────────────────────────────
def render_game_card(my_team, opponent, sel, weather, win_score):
    mc   = TEAM_COLORS.get(my_team, "#1A56DB")
    oc   = TEAM_COLORS.get(opponent, "#6B7280")
    d    = sel["날짜"].strftime("%Y. %m. %d") + f" ({sel['요일']})"
    stad = sel["구장"]
    gt   = GAME_TIME.get(sel["요일"], "18:30")
    my_p = round(win_score, 1)
    op_p = round(100 - win_score, 1)

    if weather.get("예보가능"):
        risk  = weather.get("리스크등급", "")
        emap  = {"낮음":"☀️","보통":"⛅","높음":"🌦️","매우 높음":"🌧️"}
        w_txt = f"{emap.get(risk,'')} 우천확률 {weather.get('우천확률',0)}%"
    else:
        w_txt = "📅 예보 범위 외"

    st.markdown(f"""
<div class="kbo-game-card">
  <div class="kbo-card-header">
    <div>
      <div class="kbo-date-txt">{d} · {stad}</div>
      <div class="kbo-time-txt">{gt} KST</div>
    </div>
    <div class="kbo-weather-badge">{w_txt}</div>
  </div>
  <div class="kbo-teams-row">
    <div class="kbo-team-wrap">
      <div class="kbo-team-badge" style="background:{mc};">{my_team}</div>
      <div class="kbo-team-lbl">{my_team}</div>
      <div class="kbo-team-sub">원정</div>
    </div>
    <div class="kbo-vs">VS</div>
    <div class="kbo-team-wrap">
      <div class="kbo-team-badge" style="background:{oc};">{opponent}</div>
      <div class="kbo-team-lbl">{opponent}</div>
      <div class="kbo-team-sub">홈</div>
    </div>
  </div>
  <div>
    <div class="kbo-prob-label">승리 확률</div>
    <div class="kbo-prob-bar">
      <div style="width:{my_p}%;background:{mc};height:100%;"></div>
      <div style="width:{op_p}%;background:{oc};height:100%;opacity:0.6;"></div>
    </div>
    <div class="kbo-prob-nums">
      <span class="kbo-prob-my">{my_team} {my_p}%</span>
      <span class="kbo-prob-op">{op_p}% {opponent}</span>
    </div>
  </div>
</div>
    """, unsafe_allow_html=True)

# ── 추천도 점수 카드 ──────────────────────────────────────────────────
def render_score_card(result, my_team):
    score = result["추천도"]
    grade = result["등급"]
    mc    = TEAM_COLORS.get(my_team, "#1A56DB")
    gcfg  = {
        "추천":   ("#DCFCE7","#166534","✅"),
        "보통":   ("#FEF9C3","#854D0E","📊"),
        "비추천": ("#FEE2E2","#991B1B","❌"),
    }
    g_bg, g_c, g_e = gcfg.get(grade, ("#F3F4F6","#374151",""))

    items = [
        ("⚾ 승률 예측", result["승률예측"]["점수"], "#1A56DB"),
        ("📈 최근 폼",   result["최근폼"]["점수"],   "#059669"),
        ("🤝 상대 전적", result["상대전"]["점수"],   "#7C3AED"),
        ("✈️ 원정 승률", result["원정승률"]["점수"], "#D97706"),
    ]
    bars = ""
    for lbl, s, c in items:
        bars += f"""
  <div class="kbo-bar-row">
    <span>{lbl}</span>
    <span style="font-weight:700;color:{c};">{s:.1f}점</span>
  </div>
  <div class="kbo-bar-bg">
    <div class="kbo-bar-fill" style="width:{s}%;background:{c};"></div>
  </div>"""

    st.markdown(f"""
<div class="kbo-score-card">
  <div class="kbo-score-lbl">추천도 점수</div>
  <div class="kbo-score-num" style="color:{mc};">{score:.0f}</div>
  <div class="kbo-score-sub">/ 100점</div>
  <span class="kbo-grade-badge" style="background:{g_bg};color:{g_c};">{g_e} {grade}</span>
  {bars}
</div>
    """, unsafe_allow_html=True)

# ── 추천 근거 상세 카드 ───────────────────────────────────────────────
def render_detail_card(key, data):
    info   = SCORE_EXPLANATIONS[key]
    c      = info["color"]
    bg     = info["bg"]
    cold   = data.get("콜드스타트", False)
    s_c    = "#D97706" if cold else "#059669"
    s_txt  = "⚠️ 콜드스타트" if cold else "✅ 정상"
    notice = data.get("안내문구", "")
    n_html = f"""<div style="margin-top:10px;background:#FFF7ED;border-left:3px solid #F59E0B;border-radius:0 6px 6px 0;padding:8px;font-size:10px;font-family:Noto Sans KR,sans-serif;color:#92400E;">{notice}</div>""" if notice else ""
    hr     = f'<hr style="border:none;border-top:1px solid {c}20;margin-bottom:12px;">'

    st.markdown(f"""
<div class="kbo-detail-card" style="background:{bg};border:1px solid {c}25;">
  <div class="kbo-detail-lbl">{info['icon']} {info['label']}</div>
  <div class="kbo-detail-score" style="color:{c};">{data['점수']:.0f}</div>
  <div class="kbo-detail-status" style="color:{s_c};">{s_txt}</div>
  {hr}
  <div style="font-family:Noto Sans KR,sans-serif;font-size:11px;font-weight:700;color:{c};margin-bottom:6px;">추천도 반영 비중: {info['weight']}</div>
  <div class="kbo-detail-section">📐 산출 방식</div>
  <div class="kbo-detail-content">{info['method']}</div>
  <div class="kbo-detail-section">💡 설명</div>
  <div class="kbo-detail-content">{info['desc']}</div>
  {n_html}
</div>
    """, unsafe_allow_html=True)

# ── 메인 ─────────────────────────────────────────────────────────────
def render_tab1():
    inject_css()

    if "my_team" not in st.session_state:
        st.session_state["my_team"] = "삼성"

    my_team  = st.session_state["my_team"]
    schedule = load_schedule()
    results  = load_results()
    today    = pd.Timestamp(date.today())

    away_games = schedule[
        (schedule["원정팀"] == my_team) & (schedule["날짜"] >= today)
    ].sort_values("날짜").reset_index(drop=True)

    # ── 사이드바 ─────────────────────────────────────────────────────
    with st.sidebar:
        mc = TEAM_COLORS.get(my_team, "#1A56DB")
        st.markdown(f"""
<div style="text-align:center;padding:16px 0 8px;font-family:Noto Sans KR,sans-serif;">
  <div style="width:60px;height:60px;border-radius:50%;background:{mc};
              display:inline-flex;align-items:center;justify-content:center;
              font-size:18px;font-weight:900;color:white;margin-bottom:8px;">{my_team}</div>
  <div style="font-size:14px;font-weight:700;color:#0D1B2A;">{my_team} 원정 일정</div>
</div>
        """, unsafe_allow_html=True)
        st.divider()

        if away_games.empty:
            st.info("남은 원정 경기가 없어요.")
            return

        st.caption("경기 선택")
        options = [
            f"{r['날짜'].strftime('%m/%d')} ({r['요일']}) vs {r['홈팀']} · {r['도시']}"
            for _, r in away_games.iterrows()
        ]
        sel_idx = st.selectbox("원정 경기", range(len(options)),
                               format_func=lambda i: options[i],
                               label_visibility="collapsed")
        sel = away_games.iloc[sel_idx]

        st.divider()
        st.caption("다음 원정 일정")
        for _, row in away_games.iloc[sel_idx+1:sel_idx+4].iterrows():
            rc = TEAM_COLORS.get(row["홈팀"], "#6B7280")
            gt = GAME_TIME.get(row["요일"], "18:30")
            st.markdown(f"""
<div class="kbo-sidebar-item">
  <div style="display:flex;align-items:center;gap:10px;">
    <div class="kbo-sidebar-badge" style="background:{rc};">{row['홈팀']}</div>
    <div>
      <div style="font-size:14px;font-weight:700;color:#0D1B2A;">{row['홈팀']}</div>
      <div style="font-size:12px;color:#6B7280;">{row['날짜'].strftime('%m/%d')} ({row['요일']}) {gt} · {row['도시']}</div>
    </div>
  </div>
</div>
            """, unsafe_allow_html=True)

    # ── 메인 콘텐츠 ──────────────────────────────────────────────────
    st.markdown('<div class="kbo-section-label">UPCOMING FIXTURE</div>', unsafe_allow_html=True)
    st.markdown('<div class="kbo-section-title">경기 & 예측</div>', unsafe_allow_html=True)

    game_date = sel["날짜"].strftime("%Y-%m-%d")
    opponent  = sel["홈팀"]
    stadium   = sel["구장"]
    city      = sel["도시"]

    with st.spinner("추천도 계산 중..."):
        try:
            result   = get_recommendation(my_team, opponent, stadium, game_date)
            score_ok = True
        except Exception as e:
            st.error(f"점수 계산 오류: {e}")
            score_ok = False

    if not score_ok:
        return

    weather   = result.get("날씨", {})
    win_score = result["승률예측"]["점수"]

    # 경기 카드(좌) + 추천도+상세(우)
    col_l, col_r = st.columns([3, 2], gap="large")

    with col_l:
        render_game_card(my_team, opponent, sel, weather, win_score)
        if result.get("재검토권장"):
            st.error(f"⚠️ 우천 리스크 매우 높음 ({weather.get('우천확률',0)}%) — 일정 재검토 권장")
        if weather.get("예보가능"):
            risk  = weather.get("리스크등급","낮음")
            rain  = weather.get("우천확률", 0)
            emap  = {"낮음":"☀️","보통":"⛅","높음":"🌦️","매우 높음":"🌧️"}
            cmap  = {"낮음":"#059669","보통":"#D97706","높음":"#EA580C","매우 높음":"#DC2626"}
            bgmap = {"낮음":"#DCFCE7","보통":"#FEF9C3","높음":"#FFEDD5","매우 높음":"#FEE2E2"}
            st.markdown(f"""
<div style="margin-top:8px;">
  <span style="display:inline-flex;align-items:center;gap:6px;padding:6px 14px;
               border-radius:20px;background:{bgmap.get(risk,'#F3F4F6')};
               color:{cmap.get(risk,'#374151')};
               font-family:Noto Sans KR,sans-serif;font-size:13px;font-weight:500;">
    {emap.get(risk,'')} 우천 리스크 {risk} ({rain}%)
  </span>
</div>""", unsafe_allow_html=True)
        for notice in result.get("콜드스타트_안내", []):
            st.warning(notice)

    with col_r:
        render_score_card(result, my_team)
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        with st.expander("📋 추천 근거 상세 보기", expanded=False):
            c1, c2 = st.columns(2, gap="small")
            with c1: render_detail_card("승률예측", result["승률예측"])
            with c2: render_detail_card("최근폼",   result["최근폼"])

            st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)  # 행 사이 간격

            c3, c4 = st.columns(2, gap="small")
            with c3: render_detail_card("상대전",   result["상대전"])
            with c4: render_detail_card("원정승률", result["원정승률"])

            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

    # 원정 승률 차트 (하단)
    st.markdown("---")
    st.markdown(f"**📊 {city} 원정 구장 승률 비교** · 최근 5시즌 기준 TOP 5")
    df_aw = get_away_win_rates(results, city)
    if not df_aw.empty:
        colors = [TEAM_COLORS.get(t,"#94A3B8") if t == my_team else "#CBD5E1" for t in df_aw["팀"]]
        fig = go.Figure(go.Bar(
            x=df_aw["팀"], y=df_aw["원정승률"],
            marker_color=colors, marker_line_width=0,
            text=[f"{v:.0%}" for v in df_aw["원정승률"]],
            textposition="outside",
            textfont=dict(family="Noto Sans KR", size=12, color="#374151"),
        ))
        fig.update_layout(
            paper_bgcolor="white", plot_bgcolor="white", height=260,
            margin=dict(l=0,r=0,t=16,b=0),
            yaxis=dict(tickformat=".0%", range=[0,1], gridcolor="#F3F4F6"),
            xaxis=dict(showgrid=False), showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    st.set_page_config(
        page_title="원정 응원 플래너",
        page_icon="⚾",
        layout="wide",
        initial_sidebar_state="expanded"  # 사이드바 항상 열린 상태로 시작
    )
    render_tab1()
