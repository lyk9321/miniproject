"""
KBO 2026 시즌 경기 결과 크롤러 + 기존 데이터 병합
- 실행: python crawl_kbo_2026.py
- 결과: kbo_results_all.csv (2016~2026 전체)

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
from datetime import datetime

# ── 설정 ────────────────────────────────────────────────────────────
PAST_FILE   = "kbo_results_10season.csv"   # 기존 2016~2025 파일
OUTPUT_FILE = "kbo_results_all.csv"        # 최종 병합 파일
DELAY       = 1.5

# ── 팀명 통일 매핑 ───────────────────────────────────────────────────
TEAM_MAP = {
    "LG": "LG", "두산": "두산", "KIA": "KIA", "삼성": "삼성",
    "한화": "한화", "롯데": "롯데", "SSG": "SSG", "SK": "SSG",
    "NC": "NC", "KT": "KT", "키움": "키움", "넥센": "키움",
}

SCORE_PATTERN = re.compile(r"^([가-힣A-Za-z]+?)(\d+)vs(\d+)([가-힣A-Za-z]+)$")


def parse_score(score_text: str):
    """'롯데1vs0한화' → (away_team, away_score, home_team, home_score)"""
    m = SCORE_PATTERN.match(score_text.strip())
    if not m:
        return None
    return (
        TEAM_MAP.get(m.group(1), m.group(1)),
        int(m.group(2)),
        int(m.group(3)),
        TEAM_MAP.get(m.group(4), m.group(4)),
    )


def parse_date(date_text: str, year: int):
    """'04.02(화)' → '2026-04-02'"""
    date_clean = re.sub(r"\(.*?\)", "", date_text).strip()
    parts = date_clean.split(".")
    if len(parts) != 2:
        return None
    try:
        return f"{year}-{int(parts[0]):02d}-{int(parts[1]):02d}"
    except ValueError:
        return None


def init_driver():
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
        year_select = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ddlYear"))
        ))
        year_options = [o.get_attribute("value") for o in year_select.options]
        if str(year) not in year_options:
            return []
        year_select.select_by_value(str(year))
        time.sleep(DELAY)

        month_select = Select(driver.find_element(By.ID, "ddlMonth"))
        month_options = [o.get_attribute("value") for o in month_select.options]
        month_str = f"{month:02d}"
        if month_str not in month_options:
            return []
        month_select.select_by_value(month_str)
        time.sleep(DELAY)

    except Exception as e:
        print(f"    ⚠️ {year}-{month:02d} 드롭다운 실패: {e}")
        return []

    soup  = BeautifulSoup(driver.page_source, "lxml")
    table = soup.find("table", {"class": "tbl"})
    if not table:
        return []

    results      = []
    current_date = None

    for row in table.find_all("tr"):
        cols = [td.text.strip() for td in row.find_all("td")]
        if not cols:
            continue

        if re.match(r"^\d{2}\.\d{2}\(", cols[0]):
            current_date = parse_date(cols[0], year)
            score_text   = cols[2] if len(cols) > 2 else ""
        else:
            score_text = cols[1] if len(cols) > 1 else ""

        if not current_date or not score_text:
            continue

        parsed = parse_score(score_text)
        if not parsed:
            continue

        away_team, away_score, home_score, home_team = parsed[0], parsed[1], parsed[2], parsed[3]

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


def crawl_2026() -> pd.DataFrame:
    """2026 시즌 크롤링 (개막일~현재 월까지만)"""
    print("🚀 크롬 드라이버 초기화 중...")
    driver = init_driver()

    # 현재 월까지만 크롤링 (미래 경기는 결과 없음)
    current_month = datetime.now().month
    results = []

    try:
        print(f"\n📅 2026시즌 크롤링 중 (3월 ~ {current_month}월)...")
        for month in range(3, current_month + 1):
            month_data = get_month_results(driver, 2026, month)
            results.extend(month_data)
            print(f"  {month}월: {len(month_data)}경기 수집")
    finally:
        driver.quit()

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(["날짜", "홈팀"]).reset_index(drop=True)
    print(f"  ✅ 2026시즌 합계: {len(df)}경기")
    return df


def merge_and_save(df_2026: pd.DataFrame):
    """기존 파일과 병합 후 저장"""
    print(f"\n📂 기존 파일 불러오는 중: {PAST_FILE}")
    df_past = pd.read_csv(PAST_FILE, encoding="utf-8-sig")
    df_past["날짜"] = pd.to_datetime(df_past["날짜"]).dt.strftime("%Y-%m-%d")

    df_all = pd.concat([df_past, df_2026], ignore_index=True)
    df_all = df_all.sort_values(["날짜", "홈팀"]).reset_index(drop=True)
    df_all.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\n{'='*50}")
    print(f"✅ 병합 완료: {OUTPUT_FILE}")
    print(f"총 {len(df_all)}경기 | {df_all['시즌'].min()} ~ {df_all['시즌'].max()}시즌")
    print(f"\n시즌별 경기 수:")
    print(df_all["시즌"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    df_2026 = crawl_2026()

    if df_2026.empty:
        print("❌ 2026 데이터 없음")
    else:
        merge_and_save(df_2026)
