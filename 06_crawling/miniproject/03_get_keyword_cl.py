# 참여기업 채용 공고 상세 페이지 크롤링

import time, csv, re, sys, requests
from dataclasses import dataclass, field, asdict
from typing import Optional
from bs4 import BeautifulSoup, NavigableString

# 데이터 구조
@dataclass
class JobPosting:
    url: str
    site: str
    title: str = ""
    company: str = ""
    responsibilities: str = ""   # 담당업무
    requirements: str = ""       # 자격요건
    preferred: str = ""          # 우대사항
    skills: str = ""             # 사용스킬
    note: str = ""               # 비고 (이미지공고, JS 렌더링 등)


# 공통 유틸
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}

# 사람인 핵심정보 섹션에서 나오는 UI 불필요 문자열 제거용
SARAMIN_JUNK = re.compile(
    r"(닫기\s*[-–—]*\s*(우대사항|자격요건|근무형태).*?상세|"
    r"우대사항상세보기|자격요건\s*상세보기|근무형태상세보기|"
    r"더보기|레이어\s*닫기|※.*?주세요\.?)",
    re.DOTALL
)

def fetch(url: str) -> Optional[BeautifulSoup]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"    [ERROR] {e}")
        return None

def clean(text: str) -> str:
    # 불필요한 공백 제거
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text

def collect_after(tag, stop_names=("h2", "h3", "h4")) -> str:
    # 태그 이후의 텍스트를 다음 같은 레벨 헤더 전까지 수집
    parts = []
    for sib in tag.next_siblings:
        if getattr(sib, "name", None) in stop_names:
            break
        if isinstance(sib, NavigableString):
            t = str(sib).strip()
            if t:
                parts.append(t)
        elif hasattr(sib, "get_text"):
            t = sib.get_text(separator="\n", strip=True)
            if t:
                parts.append(t)
    return clean("\n".join(parts))

#  리멤버 파서
def parse_remember(soup: BeautifulSoup, url: str) -> JobPosting:
    job = JobPosting(url=url, site="리멤버")

    # 제목
    h1 = soup.find("h1")
    job.title = h1.get_text(strip=True) if h1 else ""

    # 회사명
    co_tag = soup.find("a", href=lambda x: x and "/job/company/" in x)
    job.company = co_tag.get_text(strip=True) if co_tag else ""

    # <h3> 태그 기반 섹션 파싱
    SECTION_MAP = {
        "responsibilities": ["주요업무", "담당업무"],
        "requirements":     ["자격 요건", "자격요건"],
        "preferred":        ["우대사항"],
    }

    for h3 in soup.find_all("h3"):
        h3_text = h3.get_text(strip=True)
        for field_name, keywords in SECTION_MAP.items():
            if any(kw in h3_text for kw in keywords):
                text = collect_after(h3, stop_names=("h3", "h2"))
                if text:
                    setattr(job, field_name, text)

    # '이 포지션에 필요한 전문분야/기술' 이후의 스킬 항목 추출
    skill_heading = soup.find(
        string=lambda t: t and "전문분야" in t and "기술" in t
    )
    if skill_heading:
        # 부모 컨테이너에서 skill 태그들 수집
        container = skill_heading.parent
        # 형제나 부모의 다음 요소에서 스킬 목록 찾기
        check_node = container
        for _ in range(5):  # 최대 5단계 위로 탐색
            nxt = check_node.find_next_sibling()
            if nxt:
                candidates = nxt.get_text(separator="|", strip=True).split("|")
                skills = [s.strip() for s in candidates
                          if s.strip() and len(s.strip()) < 40
                          and s.strip() not in ("", "이 포지션에 필요한 전문분야/기술")]
                if skills:
                    job.skills = ", ".join(skills)
                    break
            check_node = check_node.parent
            if not check_node:
                break

    return job


# 사람인 파서
SARAMIN_FIELD_KEYWORDS = {
    "responsibilities": ["담당업무", "주요업무", "업무내용", "하는 일"],
    "requirements":     ["자격요건", "자격 요건", "지원자격", "지원 자격", "필수조건"],
    "preferred":        ["우대사항", "우대 사항", "우대조건"],
    "skills":           ["사용 스킬", "사용스킬", "기술스택", "기술 스택", "스킬"],
}
# 이모지 헤더 매핑
EMOJI_HEADER_MAP = {
    "responsibilities": ["📋 주요업무", "📋 담당업무", "📌 주요업무", "📌 담당업무",
                         "✅ 주요업무", "✅ 담당업무"],
    "requirements":     ["📋 자격요건", "📋 자격 요건", "📌 자격요건", "✅ 자격요건",
                         "📋 지원자격"],
    "preferred":        ["📋 우대사항", "📌 우대사항", "✅ 우대사항", "📋 우대 사항"],
    "skills":           ["📋 사용스킬", "📋 기술스택", "📌 스킬", "🛠️ 기술스택",
                         "🖥 기술스택", "💻 기술스택"],
}


def _get_saramin_detail_section(soup: BeautifulSoup):
    # 사람인 '상세요강' h2 이후 ~ 다음 h2 이전의 soup 영역 반환
    for h2 in soup.find_all("h2"):
        if "상세요강" in h2.get_text():
            # h2 이후의 형제 태그들을 가짜 soup으로 묶기
            parts = []
            for sib in h2.next_siblings:
                if getattr(sib, "name", None) == "h2":
                    break
                parts.append(str(sib))
            if parts:
                return BeautifulSoup("".join(parts), "html.parser")
    return None


def _parse_saramin_format_A(section: BeautifulSoup) -> dict:
    # 포맷 A: <table><td><strong>담당업무</strong></td><td>내용</td></table>
    result = {}
    for td in section.find_all("td"):
        header_tag = td.find(["strong", "b"])
        if not header_tag:
            continue
        header_text = header_tag.get_text(strip=True)
        for field_name, keywords in SARAMIN_FIELD_KEYWORDS.items():
            if any(kw in header_text for kw in keywords) and field_name not in result:
                # 값은 같은 행의 다음 <td> 또는 헤더 바로 다음 텍스트
                next_td = td.find_next_sibling("td")
                if next_td:
                    result[field_name] = clean(next_td.get_text(separator="\n"))
                else:
                    # 헤더 태그 이후의 텍스트
                    text_after = header_tag.get_text(strip=True)
                    siblings_text = []
                    for sib in header_tag.next_siblings:
                        if isinstance(sib, NavigableString):
                            siblings_text.append(str(sib).strip())
                        elif hasattr(sib, "get_text"):
                            siblings_text.append(sib.get_text(separator="\n", strip=True))
                    val = clean("\n".join(siblings_text))
                    if val:
                        result[field_name] = val
    return result


def _parse_saramin_format_B(section: BeautifulSoup) -> dict:
    # 포맷 B: 이모지 헤더 (📋 주요업무 등)
    result = {}
    text = section.get_text(separator="\n")
    # 모든 이모지 헤더 키워드 목록
    all_emojis = [kw for kws in EMOJI_HEADER_MAP.values() for kw in kws]
    end_pattern = "|".join(re.escape(kw) for kw in all_emojis)

    for field_name, headers in EMOJI_HEADER_MAP.items():
        if field_name in result:
            continue
        for h in headers:
            m = re.search(
                rf"{re.escape(h)}\s*\n(.*?)(?={end_pattern}|\Z)",
                text, re.DOTALL
            )
            if m:
                val = clean(m.group(1))
                # 너무 긴 경우(다른 섹션까지 포함) 첫 2000자만
                if val and len(val) < 3000:
                    result[field_name] = val
                    break
    return result


def _parse_saramin_format_C(section: BeautifulSoup) -> dict:
    # 포맷 C: 평문 텍스트 패턴 (담당업무\n ... 형식)
    result = {}
    text = section.get_text(separator="\n")

    all_kws = [kw for kws in SARAMIN_FIELD_KEYWORDS.values() for kw in kws]
    end_pattern = "|".join(re.escape(kw) for kw in all_kws)

    for field_name, keywords in SARAMIN_FIELD_KEYWORDS.items():
        if field_name in result:
            continue
        for kw in keywords:
            # 라인 시작 기준 매칭
            m = re.search(
                rf"(?m)^[ \t]*{re.escape(kw)}[ \t]*\n(.*?)(?=^[ \t]*(?:{end_pattern})[ \t]*\n|\Z)",
                text, re.DOTALL
            )
            if m:
                val = clean(m.group(1))
                if val and len(val) < 3000:
                    result[field_name] = val
                    break
    return result


def _clean_saramin_preferred(text: str) -> str:
    # 핵심 정보의 우대사항 dl 텍스트에서 UI 잡동사니 제거
    # '닫기', '우대사항상세보기' 등 UI 문자열 제거
    lines = []
    stop_words = {"더보기", "닫기", "우대사항상세보기", "자격요건상세보기",
                  "근무형태상세보기", "우대조건 레이어 닫기"}
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        # '닫기 - 우대사항 상세' 같은 패턴 제거
        if re.match(r"닫기\s*[-–—]", stripped):
            break  # 이후는 필요 없음
        if stripped in stop_words:
            continue
        lines.append(stripped)
    return "\n".join(lines).strip()


def parse_saramin(soup: BeautifulSoup, url: str) -> JobPosting:
    job = JobPosting(url=url, site="사람인")

    # 제목
    h1 = soup.find("h1")
    job.title = h1.get_text(strip=True) if h1 else ""

    # 회사명
    co_tag = (soup.select_one("a[href*='company-info']") or
               soup.select_one(".corp_name, .company_name"))
    job.company = co_tag.get_text(strip=True) if co_tag else ""

    # 상세요강 섹션 추출
    detail_section = _get_saramin_detail_section(soup)

    if detail_section:
        # 이미지 공고 감지
        imgs = detail_section.find_all("img", src=lambda s: s and (
            ".jpg" in s.lower() or ".png" in s.lower() or ".gif" in s.lower()
        ))
        all_text = detail_section.get_text(separator=" ", strip=True)

        # 텍스트가 거의 없고 이미지만 있는 경우
        meaningful_text_len = len(re.sub(r"\s+", "", all_text))
        if meaningful_text_len < 100 and imgs:
            job.note = "이미지 공고 - 텍스트 추출 불가 (원본 URL 직접 확인 필요)"
        else:
            # 포맷 A 시도 (테이블 기반)
            parsed = _parse_saramin_format_A(detail_section)
            # 포맷 B 시도 (이모지 헤더)
            if not parsed:
                parsed = _parse_saramin_format_B(detail_section)
            # 포맷 C 시도 (평문 패턴)
            if not parsed:
                parsed = _parse_saramin_format_C(detail_section)

            for f, v in parsed.items():
                setattr(job, f, v)

    # 핵심 정보 섹션 보완 (상세요강에서 못 찾은 항목)
    # 핵심 정보 섹션 찾기
    summary_h2 = None
    for h2 in soup.find_all("h2"):
        if "핵심 정보" in h2.get_text():
            summary_h2 = h2
            break

    if summary_h2:
        # dl/dt/dd 구조에서 추출
        dl_section = summary_h2.find_next("dl")
        if dl_section:
            dts = dl_section.find_all("dt")
            for dt in dts:
                dt_text = dt.get_text(strip=True)
                dd = dt.find_next_sibling("dd")
                if not dd:
                    continue
                dd_text = dd.get_text(separator="\n", strip=True)
                # UI 잡동사니 제거
                dd_text = _clean_saramin_preferred(dd_text)

                if not dd_text:
                    continue

                # 필드 매핑
                if "우대사항" in dt_text and not job.preferred:
                    job.preferred = dd_text
                elif "자격요건" in dt_text and not job.requirements:
                    job.requirements = dd_text
                elif "스킬" in dt_text and not job.skills:
                    job.skills = dd_text

    return job


#  잡코리아 파서

def parse_jobkorea(soup: BeautifulSoup, url: str) -> JobPosting:
    job = JobPosting(url=url, site="잡코리아")
    job.note = "잡코리아 상세내용은 JavaScript 렌더링 → 요약 정보만 추출됨"

    # 제목
    h1 = soup.find("h1")
    job.title = h1.get_text(strip=True) if h1 else ""

    # 회사명
    co_tag = soup.select_one(".name-corp, h2.name, .corp-name")
    if not co_tag:
        # "㈜회사명 채용정보" 패턴에서 추출
        page_title = soup.find("title")
        if page_title:
            m = re.search(r"^(.+?)\s+채용", page_title.get_text(strip=True))
            if m:
                job.company = m.group(1).strip()
    else:
        job.company = co_tag.get_text(strip=True)

    # h1 앞에 회사명 나오는 경우 처리
    if not job.company:
        h1_prev = h1.find_previous(["h2", "h3"]) if h1 else None
        if h1_prev:
            job.company = h1_prev.get_text(strip=True)

    # 요약정보 dl/dt/dd 에서 추출
    JUNK_STRINGS = {
        "더보기", "닫기", "우대조건 레이어 닫기",
        "직책 더보기 레이어 닫기",
    }
    JUNK_PATTERNS = re.compile(
        r"(우대조건\s*레이어\s*닫기|직책\s*더보기.*?닫기|더보기$)",
        re.DOTALL
    )

    def clean_jk_dd(dd_tag) -> str:
        lines = []
        for line in dd_tag.get_text(separator="\n", strip=True).split("\n"):
            stripped = line.strip()
            if not stripped or stripped in JUNK_STRINGS:
                continue
            if JUNK_PATTERNS.search(stripped):
                break
            lines.append(stripped)
        return "\n".join(lines).strip()

    # 요약정보 영역 내 dl 전체 파싱
    summary_section = soup.select_one(".summary-section, .gi-info-summary, #summary")
    if not summary_section:
        # h2/h3 기반으로 '요약정보' or '지원자격' 찾기
        for tag in soup.find_all(["h2", "h3", "h4"]):
            if '요약정보' in tag.get_text() or '지원자격' in tag.get_text():
                summary_section = tag.parent
                break

    # dl/dt/dd 전체에서 스킬, 우대 추출
    dts = soup.find_all("dt")
    for dt in dts:
        dt_text = dt.get_text(strip=True)
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        dd_text = clean_jk_dd(dd)
        if not dd_text:
            continue

        if dt_text == "스킬" and not job.skills:
            job.skills = dd_text
        elif dt_text in ("우대", "우대사항") and not job.preferred:
            job.preferred = dd_text
        elif "담당업무" in dt_text and not job.responsibilities:
            job.responsibilities = dd_text
        elif "자격요건" in dt_text and not job.requirements:
            job.requirements = dd_text

    return job


# 라우터
def parse_posting(url: str) -> JobPosting:
    if "rememberapp" in url:
        site_name, parser = "리멤버", parse_remember
    elif "saramin" in url:
        site_name, parser = "사람인", parse_saramin
    elif "jobkorea" in url:
        site_name, parser = "잡코리아", parse_jobkorea
    else:
        return JobPosting(url=url, site="기타", note="지원하지 않는 사이트")

    print(f"  [{site_name}] {url}")
    soup = fetch(url)
    if soup is None:
        return JobPosting(url=url, site=site_name, note="페이지 로딩 실패")

    try:
        return parser(soup, url)
    except Exception as e:
        return JobPosting(url=url, site=site_name, note=f"파싱 오류: {e}")


# 저장
def save_txt(jobs: list, filename: str = "job_postings.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for i, job in enumerate(jobs, 1):
            f.write("=" * 72 + "\n")
            f.write(f"[{i:02d}] {job.company} — {job.title}\n")
            f.write(f"     사이트: {job.site}\n")
            f.write(f"     URL   : {job.url}\n")
            if job.note:
                f.write(f"        비고: {job.note}\n")
            f.write("-" * 72 + "\n")

            sections = [
                ("■ 담당업무", job.responsibilities),
                ("■ 자격요건", job.requirements),
                ("■ 우대사항", job.preferred),
                ("■ 사용스킬", job.skills),
            ]
            has_content = False
            for header, content in sections:
                if content:
                    f.write(f"\n{header}\n{content}\n")
                    has_content = True

            if not has_content:
                f.write("\n  (추출된 내용 없음)\n")
            f.write("\n")

    print(f"    TXT 저장: {filename}")


def save_csv(jobs: list, filename: str = "job_postings.csv"):
    fields = ["site", "company", "title",
              "responsibilities", "requirements", "preferred", "skills",
              "note", "url"]

    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for job in jobs:
            d = asdict(job)
            writer.writerow({k: d[k] for k in fields})

    print(f"    CSV 저장: {filename}")


# URL 목록
URLS = [
    # 리멤버
    "https://career.rememberapp.co.kr/job/posting/265335",   # 1
    "https://career.rememberapp.co.kr/job/posting/268555",   # 2
    "https://career.rememberapp.co.kr/job/posting/269556",   # 3
    # 잡코리아
    "https://www.jobkorea.co.kr/Recruit/GI_Read/47412679",   # 4
    # 사람인
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=43803258",  # 5
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=44916747",  # 6  (이미지 공고)
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=49743074",  # 7
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=48963812",  # 8
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=51318997",  # 9
    # 잡코리아
    "https://www.jobkorea.co.kr/Recruit/GI_Read/47877343",   # 10
    # 사람인
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=52969995",  # 11
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=45872015",  # 12
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=41230908",  # 13
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=43563329",  # 14
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=41629120",  # 15
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=49659170",  # 16
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=53011550",  # 17
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=53011702",  # 18
    "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=41011821",  # 19
]


# 메인
if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"채용공고 크롤러 — 총 {len(URLS)}개 공고")
    print(f"{'='*60}\n")

    results = []
    for i, url in enumerate(URLS, 1):
        print(f"[{i:02d}/{len(URLS)}]", end=" ")
        job = parse_posting(url)
        results.append(job)
        time.sleep(1.5)

    print("\n─── 파일 저장 중 ───")
    save_txt(results, "job_postings.txt")
    save_csv(results, "job_postings.csv")

    # 결과 요약
    print(f"\n{'─'*60}")
    print("크롤링 결과 요약")
    print(f"{'─'*60}")

    field_names = {
        "responsibilities": "담당업무",
        "requirements":     "자격요건",
        "preferred":        "우대사항",
        "skills":           "사용스킬",
    }

    for i, job in enumerate(results, 1):
        filled = [fname for fname, fkr in field_names.items()
                  if getattr(job, fname)]
        empty  = [fkr for fname, fkr in field_names.items()
                  if not getattr(job, fname)]
        status = "✅" if len(filled) >= 2 else ("⚠️ " if filled else "❌")
        print(f"  {status} [{i:02d}] {job.company[:15]:<15} "
              f"추출: {', '.join(field_names[f] for f in filled) or '없음'}"
              + (f" | 미추출: {', '.join(empty)}" if empty else ""))
        if job.note:
            print(f"         ↳ {job.note[:60]}")

    total_ok = sum(1 for j in results if any(
        getattr(j, f) for f in field_names))
    print(f"\n  총 {total_ok}/{len(results)}개 공고에서 데이터 추출 성공")