"""
KBO 공식 사이트 경기 결과 크롤러
- 대상: 2016 ~ 2025 시즌 (10시즌)
- 출처: https://www.koreabaseball.com/Schedule/Schedule.aspx
- 실행: python crawl_kbo.py
- 결과: kbo_results_10season.csv 저장

※ 사전 설치: pip install selenium pandas webdriver-manager beautifulsoup4 lxml
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

# ── 설정 ────────────────────────────────────────────────────────────
START_YEAR  = 2016
END_YEAR    = 2025
OUTPUT_FILE = "kbo_results_10season.csv"
DELAY       = 1.5

# ── 팀명 통일 매핑 ───────────────────────────────────────────────────
TEAM_MAP = {
    "LG": "LG", "두산": "두산", "KIA": "KIA", "삼성": "삼성",
    "한화": "한화", "롯데": "롯데", "SSG": "SSG", "SK": "SSG",
    "NC": "NC", "KT": "KT", "키움": "키움", "넥센": "키움",
}

# ── 스코어 정규식 ────────────────────────────────────────────────────
# "롯데1vs0한화" → away=롯데, away_score=1, home=한화, home_score=0
SCORE_PATTERN = re.compile(r"^([가-힣A-Za-z]+?)(\d+)vs(\d+)([가-힣A-Za-z]+)$")


def parse_score(score_text: str):
    """
    '롯데1vs0한화' → (away_team, away_score, home_team, home_score)
    취소·우천 경기('롯데vs한화') → None 반환
    """
    m = SCORE_PATTERN.match(score_text.strip())
    if not m:
        return None
    away_team  = TEAM_MAP.get(m.group(1), m.group(1))
    away_score = int(m.group(2))
    home_score = int(m.group(3))
    home_team  = TEAM_MAP.get(m.group(4), m.group(4))
    return away_team, away_score, home_team, home_score


def parse_date(date_text: str, year: int):
    """
    '04.02(화)' → '2024-04-02'
    괄호 안 요일 제거 후 파싱
    """
    date_clean = re.sub(r"\(.*?\)", "", date_text).strip()  # "(화)" 제거
    parts = date_clean.split(".")
    if len(parts) != 2:
        return None
    try:
        return f"{year}-{int(parts[0]):02d}-{int(parts[1]):02d}"
    except ValueError:
        return None


def init_driver() -> webdriver.Chrome:
    """크롬 드라이버 초기화 (headless: 창 안 띄움)"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def get_month_results(driver, year: int, month: int) -> list[dict]:
    """특정 연도/월 경기 결과 크롤링"""
    driver.get("https://www.koreabaseball.com/Schedule/Schedule.aspx")
    time.sleep(DELAY)

    try:
        # 연도 선택
        year_select = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ddlYear"))
        ))
        year_options = [o.get_attribute("value") for o in year_select.options]
        if str(year) not in year_options:
            return []
        year_select.select_by_value(str(year))
        time.sleep(DELAY)

        # 월 선택 ("03" 형식 사용)
        month_select = Select(driver.find_element(By.ID, "ddlMonth"))
        month_options = [o.get_attribute("value") for o in month_select.options]
        month_str = f"{month:02d}"   # "3" → "03"
        if month_str not in month_options:
            return []
        month_select.select_by_value(month_str)
        time.sleep(DELAY)

    except Exception as e:
        print(f"    ⚠️ {year}-{month:02d} 드롭다운 실패: {e}")
        return []

    # ── 테이블 파싱 ──────────────────────────────────────────────────
    soup = BeautifulSoup(driver.page_source, "lxml")
    table = soup.find("table", {"class": "tbl"})
    if not table:
        return []

    results = []
    current_date = None

    for row in table.find_all("tr"):
        cols = [td.text.strip() for td in row.find_all("td")]
        if not cols:
            continue

        # 날짜 포함 행: col[0] = "04.02(화)" 형식
        if re.match(r"^\d{2}\.\d{2}\(", cols[0]):
            current_date = parse_date(cols[0], year)
            # 날짜 행에서도 경기 결과가 col[2]에 있음
            score_text = cols[2] if len(cols) > 2 else ""
        else:
            # 같은 날 이후 경기: col[0]=시간("18:30"), col[1]=스코어
            score_text = cols[1] if len(cols) > 1 else ""

        if not current_date or not score_text:
            continue

        parsed = parse_score(score_text)
        if not parsed:
            continue   # 취소·우천 경기 스킵

        away_team, away_score, home_team, home_score = parsed

        results.append({
            "날짜":       current_date,
            "홈팀":       home_team,
            "원정팀":     away_team,
            "홈팀득점":   home_score,
            "원정팀득점": away_score,
            "원정팀승리": 1 if away_score > home_score else 0,
            "시즌":       year,
        })

    return results


def crawl_all_seasons():
    """전체 시즌 크롤링 후 CSV 저장"""
    print("🚀 크롬 드라이버 초기화 중...")
    driver = init_driver()
    all_results = []

    try:
        for year in range(START_YEAR, END_YEAR + 1):
            year_results = []
            print(f"\n📅 {year}시즌 크롤링 중...")

            for month in range(3, 11):  # 정규시즌: 3~10월
                month_data = get_month_results(driver, year, month)
                year_results.extend(month_data)
                print(f"  {month}월: {len(month_data)}경기 수집")

            all_results.extend(year_results)
            print(f"  ✅ {year}시즌 합계: {len(year_results)}경기")

    finally:
        driver.quit()

    # ── 저장 ─────────────────────────────────────────────────────────
    df = pd.DataFrame(all_results)
    if df.empty:
        print("\n❌ 수집된 데이터 없음")
        return

    df = df.sort_values(["날짜", "홈팀"]).reset_index(drop=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\n{'='*50}")
    print(f"✅ 저장 완료: {OUTPUT_FILE}")
    print(f"총 {len(df)}경기 | {df['시즌'].min()} ~ {df['시즌'].max()}시즌")
    print(df.head(5).to_string(index=False))


if __name__ == "__main__":
    crawl_all_seasons()
