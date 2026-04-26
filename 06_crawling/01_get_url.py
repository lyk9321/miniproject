# 업태별 참여 기업의 채용 공고 url 수집(채용 사이트, 네이버 검색): 결과 12개

import csv
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# 회사명 저장 리스트
companies = [
    '(주)유니바',
    '유한회사나노웨더',
    '디플로',
    '(주)와이에이치데이타베이스',
    '경북대학교병원',
    '(주)모티버'
]

# 수집 결과를 저장할 파일명
output_csv = 'urls.csv'

# 공통 유틸
def get_soup(url):
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, 'html.parser')

def collect_all_links(soup, base_url=None):
    links = []
    for a in soup.select('a[href]'):
        href = a.get('href', '')
        if href.startswith('//'):
            href = 'https:' + href
        elif href.startswith('/') and base_url:
            href = base_url + href
        if href.startswith('http'):
            links.append(href)
    return list(dict.fromkeys(links))

# 사이트별 검색 URL 생성
def saramin_search(company):
    base = (
        'https://www.saramin.co.kr/zf_user/search'
        '?search_area=main'
        '&search_done=y'
        '&search_optional_item=n'
        '&searchType=search'
    )
    return f'{base}&searchword={quote(company)}'

def jobkorea_search(company, page=1):
    return f'https://www.jobkorea.co.kr/Search/?stext={quote(company)}&Page_No={page}'

def saramin_recruit_search(company, recruit_page=1):
    base = (
        'https://www.saramin.co.kr/zf_user/search/recruit'
        '?search_area=main'
        '&search_done=y'
        '&search_optional_item=n'
        '&searchType=search'
    )
    return f'{base}&searchword={quote(company)}&recruitPage={recruit_page}&recruitSort=relation&recruitPageCount=40&mainSearch=n'

def naver_search(company, start=1):
    q = quote(f'{company} 채용')
    return f'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&ie=utf8&query={q}&start={start}'

# 사람인: 검색결과 리스트 영역에서만 공고 링크 추출
def saramin_extract_job_links_in_list(soup):
    """
    사람인 페이지에서 '#recruit_info_list' (검색 결과 리스트) 안에 있는 공고 링크만 추출합니다.
    검색 결과가 0건이어도 페이지 전체에 추천공고가 붙는 경우가 있어,
    리스트 영역으로 범위를 제한해야 오탐이 줄어듭니다.
    """
    container = soup.select_one('#recruit_info_list')
    if not container:
        return []

    links = []
    for a in container.select('a[href]'):
        href = a.get('href', '')

        # 상대경로 처리
        if href.startswith('/'):
            href = 'https://www.saramin.co.kr' + href
        if href.startswith('//'):
            href = 'https:' + href

        # 공고 상세 패턴
        if 'rec_idx=' in href and '/zf_user/jobs' in href and 'view' in href:
            links.append(href)

    return list(dict.fromkeys(links))

def saramin_has_company_job(soup, company_name):
    container = soup.select_one('#recruit_info_list')
    if not container:
        return False

    target = company_name.replace(' ', '')

    for item in container.select('.item_recruit'):
        # 회사명은 보통 area_corp / corp_name 쪽에 있음
        corp_el = item.select_one('.area_corp') or item.select_one('.corp_name') or item.select_one('.company_name')
        corp_text = (corp_el.get_text(' ', strip=True) if corp_el else '').replace(' ', '')

        if target and target in corp_text:
            return True

    return False

# 유효한 검색결과(공고 존재) 판정
def has_saramin_jobs(soup, company_name):
    """
    기존: 페이지 전체에서 rec_idx가 보이면 공고 있음으로 판단(오탐 많음)
    변경: 검색 결과 리스트에서 공고 링크 추출 + 회사명 포함 공고가 있는지 확인
    """
    job_links = saramin_extract_job_links_in_list(soup)
    if len(job_links) == 0:
        return False

    # 회사명 검증(타회사 혼입 줄이기)
    return saramin_has_company_job(soup, company_name)

def has_jobkorea_jobs(soup):
    text = soup.get_text(' ', strip=True)

    # 결과 0건이면 무조건 False
    if '총 0건' in text or '검색결과가 없습니다' in text or '검색 결과가 없습니다' in text:
        return False

    all_links = collect_all_links(soup, base_url='https://www.jobkorea.co.kr')
    job_links = [u for u in all_links if 'jobkorea.co.kr/Recruit/GI_Read/' in u]
    return len(set(job_links)) > 0

def saramin_recruit_page_has_ai_job(soup, target_company='경북대학교병원'):
    container = soup.select_one('#recruit_info_list')
    if not container:
        return False

    keywords = ['AI', '인공지능', '데이터', '빅데이터', 'python', '머신러닝', '딥러닝', '의료영상']
    target = target_company.replace(' ', '')

    for item in container.select('.item_recruit'):
        # 회사명 영역만 추출
        corp_el = item.select_one('.area_corp') or item.select_one('.corp_name') or item.select_one('.company_name')
        corp_text = (corp_el.get_text(' ', strip=True) if corp_el else '').replace(' ', '')

        if target not in corp_text:
            continue

        # 카드 텍스트에서 키워드 검사
        item_text = item.get_text(' ', strip=True).lower()
        if any(k.lower() in item_text for k in keywords):
            return True

    return False

# 메인: companies만 사용해서 seed 선별
def build_seed_urls():
    seeds = []  # [company_query, platform, seed_url]

    print('=== seed URL 선별 시작 (companies 리스트 기반) ===')
    for idx, c in enumerate(companies, start=1):
        print(f'\n[{idx}/{len(companies)}] 검색어: "{c}"')

        # 사람인 일반 검색
        try:
            url = saramin_search(c)
            soup = get_soup(url)
            if has_saramin_jobs(soup, c):
                seeds.append([c, 'saramin', url])
                print('  - saramin OK')
            else:
                print('  - saramin 0')
        except Exception as e:
            print('  - saramin ERR:', e)
        time.sleep(1.2)

        # 잡코리아
        try:
            url = jobkorea_search(c, page=1)
            soup = get_soup(url)
            if has_jobkorea_jobs(soup):
                seeds.append([c, 'jobkorea', url])
                print('  - jobkorea OK')
            else:
                print('  - jobkorea 0')
        except Exception as e:
            print('  - jobkorea ERR:', e)
        time.sleep(1.2)

        # 사람인 recruit 탭 (병원만 시도)
        if '병원' in c:
            recruit_seed = None
            for p in range(1, 6):
                try:
                    url = saramin_recruit_search(c, recruit_page=p)
                    soup = get_soup(url)

                    # 페이지 전체 텍스트가 아니라, 공고 카드 내부에서만 AI/데이터 공고 존재 여부 확인
                    if saramin_recruit_page_has_ai_job(soup, target_company=c):
                        recruit_seed = url
                        print(f'  - saramin recruit OK (page={p})')
                        break
                    else:
                        print(f'  - saramin recruit 0 (page={p})')

                except Exception as e:
                    print(f'  - saramin recruit ERR (page={p}):', e)
                time.sleep(1.2)

            if recruit_seed:
                seeds.append([c, 'saramin', recruit_seed])

        # 네이버 seed는 위에서 seed가 하나라도 살아남았으면 추가
        if any(s[0] == c for s in seeds):
            seeds.append([c, 'naver', naver_search(c, start=1)])

    # URL 기준 중복 제거
    seen = set()
    uniq = []
    for row in seeds:
        if row[2] not in seen:
            seen.add(row[2])
            uniq.append(row)

    # 저장
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['company_query', 'platform', 'seed_url'])
        w.writerows(uniq)


if __name__ == '__main__':
    build_seed_urls()
