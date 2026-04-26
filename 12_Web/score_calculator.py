"""
추천도 최종 점수 계산 모듈
- feature_calculator.py + kbo_model.pkl + weather_api.py 통합
- Streamlit app.py에서 이 파일만 import하면 됨
- 사용법: from score_calculator import get_recommendation
- 실행: python score_calculator.py
"""

import pandas as pd
import numpy as np
import pickle
import streamlit as st
from datetime import datetime

from feature_calculator import get_recent_form_score, get_matchup_score, get_away_score
from weather_api import get_rain_probability

# ── 설정 ────────────────────────────────────────────────────────────
CSV_PATH   = "kbo_results_all.csv"
MODEL_PATH = "kbo_model.pkl"

# ── 추천도 가중치 ────────────────────────────────────────────────────
WEIGHTS = {
    "승률예측": 0.35,
    "최근폼":   0.25,
    "상대전":   0.20,
    "원정승률": 0.20,
}

# 날씨 재검토 권장 기준 (우천 확률 71% 이상)
RAIN_REVIEW_THRESHOLD = 71


# ── 데이터 로드 (캐시 적용) ───────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    """
    경기 결과 CSV 로드
    @st.cache_data → 앱 실행 중 한 번만 로드, 이후 캐시에서 반환
    """
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"])
    df = df.sort_values("날짜").reset_index(drop=True)
    return df


@st.cache_resource
def load_model() -> dict:
    """
    학습된 모델(pkl) 로드
    @st.cache_resource → 모델 객체는 resource로 캐시 (data와 구분)
    cache_resource란? DataFrame 같은 데이터가 아닌
    모델처럼 메모리에 올려두는 객체에 사용하는 캐시예요.
    """
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


# ── 승률 예측 점수 계산 ───────────────────────────────────────────────
def get_win_prob_score(
    df: pd.DataFrame,
    my_team: str,
    opponent: str,
    current_date: str,
    current_season: int,
) -> dict:
    """
    로지스틱 회귀 모델로 원정팀(my_team) 승리 확률 계산

    Returns
    -------
    {"점수": 52.3, "콜드스타트": False, "안내문구": None}
    """
    saved  = load_model()
    model  = saved["model"]
    scaler = saved["scaler"]

    cut_date = pd.to_datetime(current_date)
    season   = current_season

    def season_rate(team: str) -> float:
        """특정 팀의 해당 날짜 이전 시즌 승률"""
        games = df[
            (df["시즌"] == season) &
            (df["날짜"] < cut_date) &
            ((df["홈팀"] == team) | (df["원정팀"] == team))
        ]
        if len(games) == 0:
            return 0.5
        wins = (
            ((games["홈팀"] == team)   & (games["원정팀승리"] == 0)).sum() +
            ((games["원정팀"] == team) & (games["원정팀승리"] == 1)).sum()
        )
        return wins / len(games)

    def h2h_rate(team_a: str, team_b: str) -> float:
        """team_a의 team_b 상대 승률 (최근 3시즌)"""
        seasons = [season - 1, season - 2, season - 3]
        games = df[
            (df["시즌"].isin(seasons)) &
            (
                ((df["홈팀"] == team_a) & (df["원정팀"] == team_b)) |
                ((df["홈팀"] == team_b) & (df["원정팀"] == team_a))
            )
        ]
        if len(games) == 0:
            return 0.5
        wins = (
            ((games["홈팀"] == team_a)   & (games["원정팀승리"] == 0)).sum() +
            ((games["원정팀"] == team_a) & (games["원정팀승리"] == 1)).sum()
        )
        return wins / len(games)

    # my_team = 원정팀, opponent = 홈팀
    home_season = season_rate(opponent)
    away_season = season_rate(my_team)
    home_h2h    = h2h_rate(opponent, my_team)
    away_h2h    = h2h_rate(my_team, opponent)

    X        = np.array([[home_season, away_season, home_h2h, away_h2h]])
    X_scaled = scaler.transform(X)
    prob     = model.predict_proba(X_scaled)[0][1]   # 원정팀 승리 확률

    # 콜드 스타트: 이번 시즌 경기가 10경기 미만이면 안내
    this_games = df[
        (df["시즌"] == season) &
        (df["날짜"] < cut_date) &
        ((df["홈팀"] == my_team) | (df["원정팀"] == my_team))
    ]
    is_cold = len(this_games) < 10
    notice  = (
        f"⚠️ 시즌 초반 데이터 부족 ({len(this_games)}경기). "
        f"지난 시즌 기록을 반영했습니다."
    ) if is_cold else None

    return {
        "점수":       round(prob * 100, 1),
        "콜드스타트": is_cold,
        "안내문구":   notice,
    }


# ── 최종 추천도 계산 ─────────────────────────────────────────────────
def get_recommendation(
    my_team:        str,
    opponent:       str,
    stadium:        str,
    game_date:      str,
    current_season: int = 2026,
) -> dict:
    """
    추천도 최종 점수 계산 및 반환

    Parameters
    ----------
    my_team        : 내 응원팀 (원정팀) 예: "LG"
    opponent       : 상대 홈팀  예: "삼성"
    stadium        : 경기장명   예: "대구삼성라이온즈파크"
    game_date      : 경기 날짜  예: "2026-04-19"
    current_season : 현재 시즌  예: 2026

    Returns
    -------
    {
        "추천도":      76.3,
        "등급":        "추천",        # 추천 / 보통 / 비추천
        "재검토권장":  False,

        "승률예측":    {"점수": 52.3, "콜드스타트": False, "안내문구": None},
        "최근폼":      {"점수": 80.0, "콜드스타트": False, "안내문구": None},
        "상대전":      {"점수": 65.0, "콜드스타트": True,  "안내문구": "⚠️ ..."},
        "원정승률":    {"점수": 70.0, "콜드스타트": False, "안내문구": None},
        "날씨":        {"우천확률": 30, "리스크등급": "낮음", ...},

        "콜드스타트_안내": ["⚠️ 시즌 초반...", ...]  # 있는 것만
    }
    """
    df = load_data()

    # ── 각 점수 계산 ────────────────────────────────────────────────
    win_prob = get_win_prob_score(df, my_team, opponent, game_date, current_season)
    form     = get_recent_form_score(df, my_team, game_date, current_season)
    matchup  = get_matchup_score(df, my_team, opponent, game_date, current_season)
    away     = get_away_score(df, my_team, game_date, current_season)
    weather  = get_rain_probability(opponent, game_date)   # 홈팀 기준 구장

    # ── 추천도 최종 계산 ────────────────────────────────────────────
    # 날씨는 점수에 미포함, 경기력 4개 항목만 가중 합산
    score = (
        WEIGHTS["승률예측"] * win_prob["점수"] +
        WEIGHTS["최근폼"]   * form["점수"]     +
        WEIGHTS["상대전"]   * matchup["점수"]  +
        WEIGHTS["원정승률"] * away["점수"]
    )
    score = round(score, 1)

    # ── 추천 등급 분류 ───────────────────────────────────────────────
    if score >= 70:
        grade = "추천"
    elif score >= 50:
        grade = "보통"
    else:
        grade = "비추천"

    # ── 날씨 재검토 권장 플래그 ─────────────────────────────────────
    rain_prob      = weather.get("우천확률", 0) if weather.get("예보가능") else 0
    review_weather = rain_prob >= RAIN_REVIEW_THRESHOLD

    # ── 콜드 스타트 안내문구 수집 (있는 것만) ───────────────────────
    cold_notices = [
        v["안내문구"]
        for v in [win_prob, form, matchup, away]
        if v.get("콜드스타트") and v.get("안내문구")
    ]

    return {
        "추천도":         score,
        "등급":           grade,
        "재검토권장":     review_weather,

        "승률예측":       win_prob,
        "최근폼":         form,
        "상대전":         matchup,
        "원정승률":       away,
        "날씨":           weather,

        "콜드스타트_안내": cold_notices,
    }


# ── 테스트 실행 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    result = get_recommendation(
        my_team   = "LG",
        opponent  = "삼성",
        stadium   = "대구삼성라이온즈파크",
        game_date = "2026-04-25",
    )

    print(f"추천도:    {result['추천도']}점")
    print(f"등급:      {result['등급']}")
    print(f"재검토권장: {result['재검토권장']}")
    print(f"\n── 세부 점수 ──")
    print(f"승률예측:  {result['승률예측']['점수']}점")
    print(f"최근폼:    {result['최근폼']['점수']}점")
    print(f"상대전:    {result['상대전']['점수']}점")
    print(f"원정승률:  {result['원정승률']['점수']}점")
    print(f"\n── 날씨 ──")
    if result['날씨'].get('예보가능'):
        print(f"우천확률:  {result['날씨']['우천확률']}%")
        print(f"리스크:    {result['날씨']['리스크등급']}")
    else:
        print(result['날씨'].get('안내문구', '예보 없음'))

    if result['콜드스타트_안내']:
        print(f"\n── 콜드 스타트 안내 ──")
        for notice in result['콜드스타트_안내']:
            print(f"  {notice}")
