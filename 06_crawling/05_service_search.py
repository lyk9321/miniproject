# 전문서비스 AI 키워드로 사람인 검색 후 크롤링

import time, csv, re, sys
from dataclasses import dataclass, asdict, fields as dc_fields
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# 설정값
SEARCH_WORD   = "전문서비스 AI"    # 검색어
TOTAL_PAGES   = 54                # 총 페이지 수 (검색 결과 기준)
PAGE_SIZE     = 40                # 페이지당 공고 수 (40 고정)
DELAY_SEC     = 2.0               # 페이지 간 대기 시간(초)
HEADLESS      = True              # False: 브라우저 화면 보이기

# 출력 파일명
SAFE_KEYWORD  = re.sub(r"[^\w가-힣]", "_", SEARCH_WORD)
CSV_FILE      = f"saramin_{SAFE_KEYWORD}.csv"
TXT_FILE      = f"saramin_{SAFE_KEYWORD}.txt"


#  데이터 구조
@dataclass
class Job:
    title:      str = ""   # 공고 제목
    company:    str = ""   # 회사명
    location:   str = ""   # 근무 지역
    experience: str = ""   # 경력
    education:  str = ""   # 학력
    job_type:   str = ""   # 고용형태
    sectors:    str = ""   # 직무 카테고리
    reg_date:   str = ""   # 등록일
    deadline:   str = ""   # 마감일
    url:        str = ""   # 공고 URL


#  Selenium 드라이버 초기화
def create_driver() -> webdriver.Chrome:
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--lang=ko-KR")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
    svc = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=svc, options=opts)
    # navigator.webdriver 숨기기 (봇 탐지 우회)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"}
    )
    return driver


#  URL 생성
def make_url(page: int) -> str:
    kw = SEARCH_WORD.replace(" ", "%20")
    return (
        "https://www.saramin.co.kr/zf_user/search/recruit"
        f"?search_area=main"
        f"&search_done=y"
        f"&search_optional_item=n"
        f"&searchType=recently"
        f"&searchword={kw}"
        f"&recruitPage={page}"
        f"&recruitSort=relation"
        f"&recruitPageCount={PAGE_SIZE}"
    )


#  공고 목록 파싱
def parse_page(soup: BeautifulSoup) -> list[Job]:
    jobs = []

    # 공고 아이템
    items = soup.select("div.item_recruit")

    for item in items:
        # 광고/배너 블록 스킵
        classes = " ".join(item.get("class", []))
        if any(c in classes for c in ("banner", "ad_", "notice_")):
            continue

        job = Job()

        # 공고 제목 + URL
        title_a = item.select_one("h2.job_tit a")
        if not title_a:
            title_a = item.select_one(".job_tit a")
        if title_a:
            # 제목: title 속성 우선, 없으면 텍스트
            job.title = (title_a.get("title") or
                         title_a.get_text(strip=True))
            href = title_a.get("href", "")
            if href:
                # rec_idx 추출해서 깔끔한 URL 생성
                m = re.search(r"rec_idx=(\d+)", href)
                if m:
                    job.url = (f"https://www.saramin.co.kr"
                               f"/zf_user/jobs/view?rec_idx={m.group(1)}")
                else:
                    job.url = ("https://www.saramin.co.kr" + href
                               if href.startswith("/") else href)

        if not job.title:
            continue  # 제목 없으면 스킵

        # 근무 조건 (지역 / 경력 / 학력 / 고용형태): <div class="job_condition"> 안의 <span> 태그
        cond_div = item.select_one("div.job_condition")
        if cond_div:
            spans = cond_div.select("span")
            cond_texts = []
            for span in spans:
                # 지역은 <a> 태그 여러 개로 구성되므로 합쳐서 하나로
                links = span.select("a")
                if links:
                    cond_texts.append(" ".join(a.get_text(strip=True) for a in links))
                else:
                    t = span.get_text(strip=True)
                    if t:
                        cond_texts.append(t)

            # 순서대로 분류 (지역 -> 경력 -> 학력 -> 고용형태 순)
            for i, cond in enumerate(cond_texts):
                cond = cond.strip().replace("\xa0", " ")
                if i == 0:
                    job.location = cond
                elif i == 1:
                    job.experience = cond
                elif i == 2:
                    job.education = cond
                elif i == 3:
                    job.job_type = cond
                # 4개 초과 시 job_type에 이어붙이기
                elif i > 3 and cond:
                    job.job_type += f" / {cond}"

        # 직무 카테고리: <div class="job_sector"> 안의 <a>, <b> 태그
        sector_div = item.select_one("div.job_sector")
        if sector_div:
            # 모든 텍스트를 합쳐서 깔끔하게 정리
            raw = sector_div.get_text(separator=", ", strip=True)
            # 연속 쉼표·공백 정리
            raw = re.sub(r",\s*,", ",", raw)
            raw = re.sub(r"\s+", " ", raw).strip().strip(",").strip()
            job.sectors = raw

        # 회사명: <div class="area_corp"> > <span class="corp_name">
        corp_tag = item.select_one(".area_corp .corp_name")
        if not corp_tag:
            corp_tag = item.select_one(".corp_name")
        if corp_tag:
            job.company = corp_tag.get_text(strip=True)

        # 등록일 / 마감일: <div class="job_date"> > <span class="job_day">
        date_tag = item.select_one(".job_date .job_day")
        if not date_tag:
            date_tag = item.select_one(".job_day, .date")
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            # "등록일 26/02/09" vs "D-7" vs "~03/21(토)" vs "상시채용" 구분
            if "등록일" in date_text:
                job.reg_date = date_text.replace("등록일", "").strip()
            elif re.match(r"~|마감", date_text):
                job.deadline = date_text.lstrip("~").strip()
            elif re.match(r"D-\d+|D-day", date_text, re.I):
                job.deadline = date_text
            elif re.match(r"\d{2}/\d{2}", date_text):
                job.deadline = date_text
            else:
                job.deadline = date_text  # 상시채용, 채용시 마감 등

        # 마감일 태그 별도 확인
        deadline_tag = item.select_one(".job_date .deadline, .dday")
        if deadline_tag and not job.deadline:
            job.deadline = deadline_tag.get_text(strip=True)

        jobs.append(job)

    return jobs


#  저장
CSV_FIELDS = ["title", "company", "location", "experience",
              "education", "job_type", "sectors",
              "reg_date", "deadline", "url"]

def save_csv(jobs: list[Job], filename: str):
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for job in jobs:
            writer.writerow({k: asdict(job)[k] for k in CSV_FIELDS})
    print(f"CSV 저장 완료: {filename}  ({len(jobs):,}건)")


def save_txt(jobs: list[Job], filename: str, total_site: int):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write(f"  사람인 채용공고 수집 결과\n")
        f.write(f"  검색어   : {SEARCH_WORD}\n")
        f.write(f"  수집일시 : {now}\n")
        f.write(f"  사이트   : 총 {total_site:,}건\n")
        f.write(f"  수집결과 : {len(jobs):,}건\n")
        f.write("=" * 70 + "\n\n")

        for i, job in enumerate(jobs, 1):
            f.write(f"[{i:04d}] {job.title}\n")
            f.write(f"  회사명   : {job.company}\n")
            f.write(f"  지역     : {job.location}\n")
            f.write(f"  경력     : {job.experience}\n")
            f.write(f"  학력     : {job.education}\n")
            f.write(f"  고용형태 : {job.job_type}\n")
            f.write(f"  직무     : {job.sectors}\n")
            f.write(f"  등록일   : {job.reg_date}\n")
            f.write(f"  마감일   : {job.deadline}\n")
            f.write(f"  URL      : {job.url}\n")
            f.write("-" * 70 + "\n")

    print(f"TXT 저장 완료: {filename}  ({len(jobs):,}건)")


#  메인 크롤러
def run():
    print(f"\n{'='*65}")
    print(f"  사람인 채용공고 크롤러")
    print(f"  검색어: '{SEARCH_WORD}'  |  목표: {TOTAL_PAGES}페이지 전체")
    print(f"{'='*65}\n")

    driver = create_driver()    # Chrome 드라이버 초기화

    all_jobs: list[Job] = []
    seen_urls: set[str] = set()   # 중복 제거
    total_site = 0

    try:
        for page in range(1, TOTAL_PAGES + 1):
            url = make_url(page)
            print(f"  [페이지 {page:2d}/{TOTAL_PAGES}] ", end="", flush=True)

            driver.get(url)

            # 공고 목록이 로드될 때까지 대기
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.item_recruit")
                    )
                )
            except TimeoutException:
                print("타임아웃 — 공고 없음 또는 차단됨, 스킵")
                time.sleep(3)
                continue

            time.sleep(1.2)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # 첫 페이지: 총 건수 파악
            if page == 1:
                cnt_tag = soup.select_one(
                    ".cnt_result .cnt strong, "
                    "em.cnt, .search_count strong, "
                    ".total_count"
                )
                if cnt_tag:
                    m = re.search(r"[\d,]+", cnt_tag.get_text())
                    if m:
                        total_site = int(m.group().replace(",", ""))
                print(f"총 {total_site:,}건 확인\n")
                print(f"  {'페이지':^8} {'현재 수집':^10} {'신규':^8} {'누적':^10}")
                print(f"  {'─'*8} {'─'*10} {'─'*8} {'─'*10}")

            # 파싱
            page_jobs = parse_page(soup)

            # 중복 제거하며 추가
            new = 0
            for job in page_jobs:
                key = job.url or f"{job.title}||{job.company}"
                if key not in seen_urls:
                    seen_urls.add(key)
                    all_jobs.append(job)
                    new += 1

            print(f"  {page:^8} {len(page_jobs):^10} {new:^8} {len(all_jobs):^10}")

            # 마지막 페이지가 아닐 때만 대기
            if page < TOTAL_PAGES:
                time.sleep(DELAY_SEC)

    except KeyboardInterrupt:
        print(f"\n\n  중단됨 (Ctrl+C) — {len(all_jobs)}건 저장 진행")

    finally:
        driver.quit()

    # 저장
    save_csv(all_jobs, CSV_FILE)
    save_txt(all_jobs, TXT_FILE, total_site)

    # 최종 요약
    print(f"\n{'='*65}")
    print(f"     크롤링 완료")
    print(f"  검색어      : {SEARCH_WORD}")
    print(f"  수집 건수   : {len(all_jobs):,}건")
    print(f"  저장 파일   :")
    print(f"    CSV → {CSV_FILE}")
    print(f"    TXT → {TXT_FILE}")

if __name__ == "__main__":
    run()
