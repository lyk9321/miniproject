"""
추천도 점수 계산 모듈
- 최근폼점수, 상대전점수, 원정승률점수 계산
- 콜드 스타트 처리 (시즌 초반 데이터 부족 시 지난 시즌과 혼합)
- 사용법: from feature_calculator import get_scores
"""

import pandas as pd

# ── 콜드 스타트 기준 경기 수 ──────────────────────────────────────────
FORM_MIN_GAMES      = 10   # 최근폼: 10경기 미만이면 혼합
MATCHUP_MIN_GAMES   = 5    # 상대전: 5경기 미만이면 지난 3시즌 대체
AWAY_MIN_GAMES      = 10   # 원정승률: 10경기 미만이면 혼합


def load_data(csv_path: str) -> pd.DataFrame:
    """
    크롤링한 CSV 불러오기
    날짜 컬럼을 datetime으로 변환해서 정렬
    """
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"])   # 문자열 → 날짜 타입으로 변환
    df = df.sort_values("날짜").reset_index(drop=True)
    return df


def get_recent_form_score(
    df: pd.DataFrame,
    team: str,
    current_date: str,
    current_season: int,
) -> dict:
    """
    특정 팀의 특정 날짜 기준 최근폼점수 계산

    Parameters
    ----------
    df            : 전체 경기 결과 DataFrame
    team          : 팀명 (예: "LG")
    current_date  : 기준 날짜 문자열 (예: "2026-04-19")
    current_season: 현재 시즌 연도 (예: 2026)

    Returns
    -------
    {
        "점수": 65.0,          # 0~100점
        "이번시즌_경기수": 8,
        "콜드스타트": True,    # 시즌 초반 여부
        "안내문구": "⚠️ 시즌 초반..."  # 콜드스타트 시에만
    }
    """
    cut_date = pd.to_datetime(current_date)

    # ── 이번 시즌 해당 팀 경기만 필터링 ────────────────────────────
    # 홈팀이든 원정팀이든 모두 포함
    this_season = df[
        (df["시즌"] == current_season) &
        (df["날짜"] < cut_date) &          # 기준 날짜 이전 경기만
        ((df["홈팀"] == team) | (df["원정팀"] == team))
    ].copy()

    this_game_count = len(this_season)

    # ── 이번 시즌 승률 계산 함수 (내부용) ───────────────────────────
    def calc_win_rate(games: pd.DataFrame) -> float:
        """해당 팀의 경기 목록에서 승률 계산"""
        if len(games) == 0:
            return 0.0
        wins = (
            # 홈팀으로 이긴 경우
            ((games["홈팀"] == team) & (games["원정팀승리"] == 0)).sum() +
            # 원정팀으로 이긴 경우
            ((games["원정팀"] == team) & (games["원정팀승리"] == 1)).sum()
        )
        return wins / len(games)

    # ── 이번 시즌 최근 10경기 승률 ──────────────────────────────────
    recent_10 = this_season.tail(10)          # 가장 최근 10경기
    this_win_rate = calc_win_rate(recent_10)

    # ── 콜드 스타트 처리 ─────────────────────────────────────────────
    is_cold_start = this_game_count < FORM_MIN_GAMES

    if is_cold_start:
        # 지난 시즌 최근 10경기 승률 계산
        last_season = df[
            (df["시즌"] == current_season - 1) &
            ((df["홈팀"] == team) | (df["원정팀"] == team))
        ]
        last_10       = last_season.tail(10)
        last_win_rate = calc_win_rate(last_10)

        # 가중 평균: 이번 시즌 비중은 경기 수 / 10
        # 예: 이번 시즌 3경기 → 이번 시즌 30%, 지난 시즌 70%
        this_weight = this_game_count / FORM_MIN_GAMES
        last_weight = 1 - this_weight

        final_win_rate = (this_win_rate * this_weight) + (last_win_rate * last_weight)

        notice = (
            f"⚠️ 시즌 초반이라 데이터가 부족합니다 ({this_game_count}경기). "
            f"지난 시즌 기록을 {last_weight*100:.0f}% 반영하여 계산했습니다."
        )
    else:
        final_win_rate = this_win_rate
        notice = None

    return {
        "점수":           round(final_win_rate * 100, 1),  # 승률 → 0~100점
        "이번시즌_경기수": this_game_count,
        "콜드스타트":      is_cold_start,
        "안내문구":        notice,
    }


def get_matchup_score(
    df: pd.DataFrame,
    my_team: str,
    opponent: str,
    current_date: str,
    current_season: int,
) -> dict:
    """
    두 팀 간 상대전 점수 계산

    이번 시즌 맞대결 경기 수가 5경기 미만이면
    → 최근 3시즌 상대전 기록으로 대체
    """
    cut_date = pd.to_datetime(current_date)

    def get_matchup_games(seasons: list[int], before_date=None) -> pd.DataFrame:
        """특정 시즌들의 두 팀 맞대결 경기 필터링"""
        mask = (
            (df["시즌"].isin(seasons)) &
            (
                ((df["홈팀"] == my_team)   & (df["원정팀"] == opponent)) |
                ((df["홈팀"] == opponent)  & (df["원정팀"] == my_team))
            )
        )
        if before_date:
            mask &= (df["날짜"] < before_date)
        return df[mask].copy()

    def calc_matchup_win_rate(games: pd.DataFrame) -> float:
        """my_team 기준 상대전 승률"""
        if len(games) == 0:
            return 0.5   # 데이터 없으면 50% (중립값)
        wins = (
            ((games["홈팀"] == my_team)   & (games["원정팀승리"] == 0)).sum() +
            ((games["원정팀"] == my_team) & (games["원정팀승리"] == 1)).sum()
        )
        return wins / len(games)

    # 이번 시즌 맞대결
    this_matchup = get_matchup_games([current_season], before_date=cut_date)
    this_count   = len(this_matchup)

    if this_count >= MATCHUP_MIN_GAMES:
        # 데이터 충분 → 이번 시즌만 사용
        win_rate  = calc_matchup_win_rate(this_matchup)
        is_cold   = False
        notice    = None
    else:
        # 데이터 부족 → 최근 3시즌 상대전으로 대체
        past_seasons  = [current_season - 1, current_season - 2, current_season - 3]
        past_matchup  = get_matchup_games(past_seasons)
        win_rate      = calc_matchup_win_rate(past_matchup)
        is_cold       = True
        notice        = (
            f"⚠️ 이번 시즌 맞대결 데이터 부족 ({this_count}경기). "
            f"최근 3시즌 상대전 기록을 사용했습니다."
        )

    return {
        "점수":           round(win_rate * 100, 1),
        "이번시즌_경기수": this_count,
        "콜드스타트":      is_cold,
        "안내문구":        notice,
    }


def get_away_score(
    df: pd.DataFrame,
    team: str,
    current_date: str,
    current_season: int,
) -> dict:
    """
    원정 승률 점수 계산
    이번 시즌 원정 경기 수가 10경기 미만이면 지난 시즌과 가중 평균
    """
    cut_date = pd.to_datetime(current_date)

    def get_away_games(season: int, before_date=None) -> pd.DataFrame:
        """해당 팀의 원정 경기만 필터링"""
        mask = (df["시즌"] == season) & (df["원정팀"] == team)
        if before_date:
            mask &= (df["날짜"] < before_date)
        return df[mask].copy()

    def calc_away_win_rate(games: pd.DataFrame) -> float:
        if len(games) == 0:
            return 0.0
        return games["원정팀승리"].mean()   # 원정팀승리 컬럼의 평균 = 원정 승률

    # 이번 시즌 원정 경기
    this_away       = get_away_games(current_season, before_date=cut_date)
    this_count      = len(this_away)
    this_win_rate   = calc_away_win_rate(this_away)

    is_cold_start = this_count < AWAY_MIN_GAMES

    if is_cold_start:
        last_away      = get_away_games(current_season - 1)
        last_win_rate  = calc_away_win_rate(last_away)

        this_weight    = this_count / AWAY_MIN_GAMES
        last_weight    = 1 - this_weight
        final_win_rate = (this_win_rate * this_weight) + (last_win_rate * last_weight)

        notice = (
            f"⚠️ 시즌 초반 원정 경기 부족 ({this_count}경기). "
            f"지난 시즌 원정 기록을 {last_weight*100:.0f}% 반영했습니다."
        )
    else:
        final_win_rate = this_win_rate
        notice = None

    return {
        "점수":           round(final_win_rate * 100, 1),
        "이번시즌_경기수": this_count,
        "콜드스타트":      is_cold_start,
        "안내문구":        notice,
    }


def get_all_scores(
    csv_path: str,
    my_team: str,
    opponent: str,
    current_date: str,
    current_season: int,
) -> dict:
    """
    세 가지 점수를 한 번에 계산해서 반환

    사용 예시:
    result = get_all_scores(
        csv_path       = "kbo_results_10season.csv",
        my_team        = "LG",
        opponent       = "삼성",
        current_date   = "2026-04-19",
        current_season = 2026,
    )
    print(result)
    """
    df = load_data(csv_path)

    form    = get_recent_form_score(df, my_team, current_date, current_season)
    matchup = get_matchup_score(df, my_team, opponent, current_date, current_season)
    away    = get_away_score(df, my_team, current_date, current_season)

    return {
        "최근폼점수":   form,
        "상대전점수":   matchup,
        "원정승률점수": away,
    }


# ── 테스트 실행 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    result = get_all_scores(
        csv_path       = "kbo_results_10season.csv",
        my_team        = "LG",
        opponent       = "삼성",
        current_date   = "2026-04-19",
        current_season = 2026,
    )

    for key, val in result.items():
        print(f"\n── {key} ──")
        for k, v in val.items():
            print(f"  {k}: {v}")
