"""
KBO 승률 예측 로지스틱 회귀 모델 학습
- 입력: kbo_results_all.csv (2016~2026)
- 출력: kbo_model.pkl (학습된 모델)
- 실행: python model_trainer.py
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

# ── 설정 ────────────────────────────────────────────────────────────
CSV_PATH   = "kbo_results_all.csv"
MODEL_PATH = "kbo_model.pkl"


# ── 1. 데이터 로드 ───────────────────────────────────────────────────
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"])
    df = df.sort_values("날짜").reset_index(drop=True)
    return df


# ── 2. 피처 엔지니어링 ────────────────────────────────────────────────
"""
피처 엔지니어링이란?
원시 데이터(날짜, 팀명, 점수)를 모델이 학습할 수 있는
숫자 형태의 의미 있는 값으로 변환하는 과정이에요.

예시:
  원시 데이터: "2024-04-15, LG vs 삼성"
  피처:        홈팀(LG) 시즌승률=0.60, 원정팀(삼성) 시즌승률=0.45 ...

중요: 각 경기의 피처는 반드시 "그 경기 이전 데이터"로만 계산해야 해요.
     미래 데이터를 쓰면 실제 예측에서 사용할 수 없는 허구의 모델이 됨.
     (이를 데이터 누수/Data Leakage 라고 해요)
"""

def calc_team_win_rate(df: pd.DataFrame, team: str,
                       season: int, before_date) -> float:
    """
    특정 팀의 특정 날짜 이전 시즌 승률 계산
    홈/원정 구분 없이 전체 경기 기준
    """
    games = df[
        (df["시즌"] == season) &
        (df["날짜"] < before_date) &
        ((df["홈팀"] == team) | (df["원정팀"] == team))
    ]
    if len(games) == 0:
        return 0.5   # 데이터 없으면 중립값 (50%)

    wins = (
        ((games["홈팀"] == team)    & (games["원정팀승리"] == 0)).sum() +
        ((games["원정팀"] == team)  & (games["원정팀승리"] == 1)).sum()
    )
    return wins / len(games)


def calc_head_to_head_rate(df: pd.DataFrame, team_a: str,
                           team_b: str, before_date,
                           n_seasons: int = 3) -> float:
    """
    team_a의 team_b 상대 승률 계산 (최근 n_seasons 시즌 기준)
    데이터 누수 방지: before_date 이전 데이터만 사용
    """
    current_season = before_date.year
    target_seasons = list(range(current_season - n_seasons, current_season + 1))

    games = df[
        (df["시즌"].isin(target_seasons)) &
        (df["날짜"] < before_date) &
        (
            ((df["홈팀"] == team_a) & (df["원정팀"] == team_b)) |
            ((df["홈팀"] == team_b) & (df["원정팀"] == team_a))
        )
    ]
    if len(games) == 0:
        return 0.5   # 데이터 없으면 중립값

    wins = (
        ((games["홈팀"] == team_a)    & (games["원정팀승리"] == 0)).sum() +
        ((games["원정팀"] == team_a)  & (games["원정팀승리"] == 1)).sum()
    )
    return wins / len(games)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    전체 데이터셋에 피처 4개 추가
    - 홈팀_시즌승률
    - 원정팀_시즌승률
    - 홈팀_상대전승률  (홈팀 기준 원정팀 상대 승률)
    - 원정팀_상대전승률 (원정팀 기준 홈팀 상대 승률)

    ※ 각 경기마다 루프를 돌기 때문에 시간이 조금 걸려요 (약 1~2분)
    """
    print("피처 엔지니어링 중... (약 1~2분 소요)")

    home_season_rates  = []
    away_season_rates  = []
    home_h2h_rates     = []
    away_h2h_rates     = []

    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"  {idx}/{len(df)} 완료...")

        date       = row["날짜"]
        home_team  = row["홈팀"]
        away_team  = row["원정팀"]
        season     = row["시즌"]

        # 홈팀/원정팀 시즌 승률 (이 경기 이전까지)
        home_rate  = calc_team_win_rate(df, home_team, season, date)
        away_rate  = calc_team_win_rate(df, away_team, season, date)

        # 상대전 승률 (최근 3시즌 기준)
        home_h2h   = calc_head_to_head_rate(df, home_team, away_team, date)
        away_h2h   = calc_head_to_head_rate(df, away_team, home_team, date)

        home_season_rates.append(home_rate)
        away_season_rates.append(away_rate)
        home_h2h_rates.append(home_h2h)
        away_h2h_rates.append(away_h2h)

    df = df.copy()
    df["홈팀_시즌승률"]    = home_season_rates
    df["원정팀_시즌승률"]  = away_season_rates
    df["홈팀_상대전승률"]  = home_h2h_rates
    df["원정팀_상대전승률"] = away_h2h_rates

    return df


# ── 3. 모델 학습 ─────────────────────────────────────────────────────
def train_model(df: pd.DataFrame):
    """
    로지스틱 회귀 모델 학습 및 평가

    피처(X): 홈팀_시즌승률, 원정팀_시즌승률, 홈팀_상대전승률, 원정팀_상대전승률
    타겟(y): 원정팀승리 (1=원정팀 승, 0=홈팀 승)
    """
    FEATURES = ["홈팀_시즌승률", "원정팀_시즌승률", "홈팀_상대전승률", "원정팀_상대전승률"]

    X = df[FEATURES].values
    y = df["원정팀승리"].values

    # 시계열 데이터라 shuffle=False (과거 → 미래 순서 유지)
    # 2026 시즌은 테스트용으로 분리
    train_mask = df["시즌"] < 2026
    test_mask  = df["시즌"] == 2026

    X_train, y_train = X[train_mask], y[train_mask]
    X_test,  y_test  = X[test_mask],  y[test_mask]

    print(f"\n학습 데이터: {len(X_train)}경기 (2016~2025)")
    print(f"테스트 데이터: {len(X_test)}경기 (2026)")

    # 스케일링: 피처 값 범위를 0~1로 맞춰줌
    # 로지스틱 회귀는 스케일에 민감하기 때문에 필요해요
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)   # 학습 데이터로 기준 맞춤
    X_test  = scaler.transform(X_test)        # 같은 기준으로 테스트 변환

    # 로지스틱 회귀 학습
    model = LogisticRegression(
        max_iter=1000,    # 수렴할 때까지 최대 반복 횟수
        random_state=42,  # 재현성을 위한 시드값
    )
    model.fit(X_train, y_train)

    # 성능 평가
    y_pred = model.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    print(f"\n테스트 정확도: {acc:.3f} ({acc*100:.1f}%)")
    print(f"\n분류 리포트:")
    print(classification_report(y_test, y_pred,
                                 target_names=["홈팀 승", "원정팀 승"]))

    # 피처 중요도 (계수) 출력
    print("피처별 영향력 (계수):")
    for feat, coef in zip(FEATURES, model.coef_[0]):
        direction = "↑ 원정팀 유리" if coef > 0 else "↓ 홈팀 유리"
        print(f"  {feat:<15}: {coef:+.4f}  {direction}")

    return model, scaler


# ── 4. 모델 저장 ─────────────────────────────────────────────────────
def save_model(model, scaler, path: str):
    """
    학습된 모델과 스케일러를 pkl 파일로 저장
    pkl이란? 파이썬 객체를 파일로 저장하는 형식이에요.
    나중에 불러와서 바로 예측에 사용할 수 있어요.
    """
    with open(path, "wb") as f:
        pickle.dump({"model": model, "scaler": scaler}, f)
    print(f"\n✅ 모델 저장 완료: {path}")


# ── 5. 예측 함수 (Streamlit에서 호출) ────────────────────────────────
def predict_win_probability(
    model_path: str,
    home_season_rate:  float,
    away_season_rate:  float,
    home_h2h_rate:     float,
    away_h2h_rate:     float,
) -> float:
    """
    저장된 모델로 원정팀 승리 확률 예측 → 0~100점 반환

    Parameters
    ----------
    home_season_rate : 홈팀 이번 시즌 승률 (0~1)
    away_season_rate : 원정팀 이번 시즌 승률 (0~1)
    home_h2h_rate    : 홈팀의 원정팀 상대 승률 (0~1)
    away_h2h_rate    : 원정팀의 홈팀 상대 승률 (0~1)

    Returns
    -------
    float: 원정팀 승리 확률 점수 (0~100)
    """
    with open(model_path, "rb") as f:
        saved = pickle.load(f)

    model  = saved["model"]
    scaler = saved["scaler"]

    X = np.array([[home_season_rate, away_season_rate,
                   home_h2h_rate,    away_h2h_rate]])
    X_scaled = scaler.transform(X)

    # predict_proba → [홈팀승 확률, 원정팀승 확률]
    prob = model.predict_proba(X_scaled)[0][1]   # 원정팀 승리 확률
    return round(prob * 100, 1)                   # 0~100점으로 변환


# ── 실행 ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== KBO 승률 예측 모델 학습 ===\n")

    df       = load_data(CSV_PATH)
    df       = build_features(df)
    model, scaler = train_model(df)
    #save_model(model, scaler, MODEL_PATH)

    # 예측 테스트
    print("\n=== 예측 테스트 ===")
    score = predict_win_probability(
        model_path       = MODEL_PATH,
        home_season_rate = 0.55,   # 홈팀 시즌 승률 55%
        away_season_rate = 0.60,   # 원정팀 시즌 승률 60%
        home_h2h_rate    = 0.40,   # 홈팀 상대전 승률 40%
        away_h2h_rate    = 0.60,   # 원정팀 상대전 승률 60%
    )
    print(f"원정팀 승리 확률 점수: {score}점")
