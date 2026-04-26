"""
기상청 단기예보 API 연동 모듈
- 서비스명: 기상청_단기예보 조회서비스 (VilageFcstInfoService_2.0)
- 예보 범위: 최대 5~6일 (발표 시각에 따라 다름)
- 격자 좌표 출처: 기상청 격자_위경도 공식 파일 (읍면동 단위 기준)
"""

import requests
import os
from datetime import datetime, timedelta

# ── API 설정 ─────────────────────────────────────────────────────────
API_KEY = os.getenv("ANTHROPIC_API_KEY")
BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

# ── 단기예보 최대 조회 가능일 수 ──────────────────────────────────────
MAX_FORECAST_DAYS = 6

# ── KBO 구장별 기상청 격자 좌표 ───────────────────────────────────────
# 출처: 기상청 격자_위경도 파일 (읍면동 단위)
# 구단명(CSV) → 구장명 → 행정동 → (nx, ny)
STADIUM_GRID = {
    # 구장명: 행정동 기준
    "광주-기아 챔피언스 필드": {   # 광주광역시 북구 임동
        "nx": 59, "ny": 74, "도시": "광주",
        "팀": ["KIA"]
    },
    "대구삼성라이온즈파크": {       # 대구광역시 수성구 (연호동 미수록 → 수성구 기준)
        "nx": 89, "ny": 90, "도시": "대구",
        "팀": ["삼성"]
    },
    "잠실야구장": {                 # 서울특별시 송파구 잠실2동
        "nx": 62, "ny": 126, "도시": "서울",
        "팀": ["LG", "두산"]
    },
    "수원 케이티 위즈 파크": {      # 경기도 수원시 장안구 조원1동
        "nx": 61, "ny": 121, "도시": "수원",
        "팀": ["KT"]
    },
    "인천 SSG랜더스필드": {         # 인천광역시 미추홀구 문학동
        "nx": 55, "ny": 124, "도시": "인천",
        "팀": ["SSG"]
    },
    "사직야구장": {                 # 부산광역시 동래구 사직제1동
        "nx": 98, "ny": 76, "도시": "부산",
        "팀": ["롯데"]
    },
    "한화생명 이글스파크": {         # 대전광역시 중구 부사동
        "nx": 68, "ny": 100, "도시": "대전",
        "팀": ["한화"]
    },
    "창원NC파크": {                  # 경상남도 창원시 마산회원구 양덕1동
        "nx": 89, "ny": 77, "도시": "창원",
        "팀": ["NC"]
    },
    "고척스카이돔": {               # 서울특별시 구로구 고척제1동
        "nx": 58, "ny": 125, "도시": "서울",
        "팀": ["키움"]
    },
}

# ── 팀명 → 구장명 역방향 매핑 ─────────────────────────────────────────
# 팀명으로 바로 조회할 수 있도록
TEAM_TO_STADIUM = {
    team: stadium
    for stadium, info in STADIUM_GRID.items()
    for team in info["팀"]
}


def get_base_datetime() -> tuple[str, str]:
    """
    현재 시각 기준 가장 최근 발표 시간 계산
    기상청 발표 시각: 02·05·08·11·14·17·20·23시
    (각 발표 후 10분 뒤부터 데이터 제공)
    """
    now         = datetime.now()
    issue_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    base_hour   = 23
    base_date   = now

    for h in issue_hours:
        if now.hour >= h:
            base_hour = h

    # 자정~02시 사이면 전날 23시 발표 기준
    if now.hour < 2:
        base_date = now - timedelta(days=1)
        base_hour = 23

    return base_date.strftime("%Y%m%d"), f"{base_hour:02d}00"


def is_forecast_available(target_date: str) -> bool:
    """오늘로부터 MAX_FORECAST_DAYS일 이내인지 확인"""
    today  = datetime.now().date()
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    diff   = (target - today).days
    return 0 <= diff <= MAX_FORECAST_DAYS


def get_rain_probability(home_team: str, target_date: str) -> dict:
    """
    홈팀명으로 해당 구장의 강수확률 조회

    Parameters
    ----------
    home_team   : 홈팀명 (예: "LG", "삼성", "NC")
    target_date : 경기 날짜 (예: "2026-04-19")

    Returns
    -------
    예보 가능한 경우:
    {
        "우천확률":   30,
        "리스크등급": "보통",       # 낮음 / 보통 / 높음 / 매우 높음
        "리스크색상": "yellow",     # green / yellow / orange / red
        "재검토권장": False,        # True면 ⚠️ 플래그 표시 (71%↑)
        "구장":       "잠실야구장",
        "도시":       "서울",
        "날짜":       "2026-04-19",
        "예보가능":   True
    }

    예보 범위 초과:
    {
        "예보가능": False,
        "안내문구": "단기예보는 최대 6일 이내만 제공됩니다.",
        ...
    }
    """
    # ── 구장 확인 ─────────────────────────────────────────────────────
    if home_team not in TEAM_TO_STADIUM:
        return {"에러": f"'{home_team}' 팀 정보 없음. 가능한 팀: {list(TEAM_TO_STADIUM.keys())}"}

    stadium_name = TEAM_TO_STADIUM[home_team]
    grid         = STADIUM_GRID[stadium_name]
    nx, ny       = grid["nx"], grid["ny"]

    # ── 예보 가능 날짜 확인 ───────────────────────────────────────────
    if not is_forecast_available(target_date):
        today  = datetime.now().date()
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
        diff   = (target - today).days
        return {
            "예보가능": False,
            "안내문구": (
                f"단기예보는 최대 {MAX_FORECAST_DAYS}일 이내만 제공됩니다. "
                f"({diff}일 후 경기)"
            ),
            "구장": stadium_name,
            "도시": grid["도시"],
            "날짜": target_date,
        }

    base_date, base_time = get_base_datetime()

    # ── API 요청 ──────────────────────────────────────────────────────
    params = {
        "serviceKey": API_KEY,
        "pageNo":     "1",
        "numOfRows":  "1000",
        "dataType":   "JSON",
        "base_date":  base_date,
        "base_time":  base_time,
        "nx":         str(nx),
        "ny":         str(ny),
    }

    try:
        resp  = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json()["response"]["body"]["items"]["item"]
    except Exception as e:
        return {"에러": f"API 요청 실패: {str(e)}", "예보가능": False}

    # ── 강수확률(POP) 파싱 ───────────────────────────────────────────
    # 경기 시간대(17~19시) 기준, KBO 경기 보통 18:30 시작
    target_yyyymmdd = target_date.replace("-", "")

    rain_probs = [
        int(item["fcstValue"])
        for item in items
        if (
            item["category"] == "POP" and
            item["fcstDate"] == target_yyyymmdd and
            item["fcstTime"] in ["1700", "1800", "1900"]
        )
    ]

    # 경기 시간대 데이터 없으면 해당 날 전체 평균으로 대체
    if not rain_probs:
        rain_probs = [
            int(item["fcstValue"])
            for item in items
            if item["category"] == "POP" and item["fcstDate"] == target_yyyymmdd
        ]

    rain_prob = round(sum(rain_probs) / len(rain_probs)) if rain_probs else 0

    # ── 리스크 등급 분류 ──────────────────────────────────────────────
    if rain_prob <= 30:
        grade, color, review = "낮음",      "green",  False
    elif rain_prob <= 50:
        grade, color, review = "보통",      "yellow", False
    elif rain_prob <= 70:
        grade, color, review = "높음",      "orange", False
    else:
        grade, color, review = "매우 높음", "red",    True

    return {
        "우천확률":   rain_prob,
        "리스크등급": grade,
        "리스크색상": color,
        "재검토권장": review,
        "구장":       stadium_name,
        "도시":       grid["도시"],
        "날짜":       target_date,
        "예보가능":   True,
    }


# ── 테스트 ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== 예보 가능한 경기 ===")
    print(get_rain_probability("LG", "2026-04-19"))

    print("\n=== 예보 범위 초과 경기 ===")
    print(get_rain_probability("삼성", "2026-05-30"))
