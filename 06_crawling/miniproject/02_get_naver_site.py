# 업태별 참여 기업의 채용 공고 url 수집(네이버 사이트 검색): 결과 43개

import csv
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

companies = [
    '(주)유니바',
    '(유)나노웨더',
    '디플로',
    '(주)와이에이치데이타베이스',
    '경북대학교병원',
    '(주)모티버'
]

sites = ['saramin.co.kr', 'jobkorea.co.kr']
starts = [1]
output_csv = 'naver_site_urls_dedup.csv'

# 네이버 site 검색 URL 생성
def naver_site_search_url(company, site, start=1):
    query = f'site:{site} "{company}"'
    return (
        'https://search.naver.com/search.naver'
        f'?where=web&sm=tab_pge&query={quote(query)}&start={start}'
    )

# 네이버 결과 제목 링크만 추출
def extract_naver_result_links(soup):
    selectors = ['a.api_txt_lines', 'a.link_tit', 'a.total_tit']
    links = []

    for sel in selectors:
        for a in soup.select(sel):
            href = a.get('href', '')
            if href.startswith('http'):
                links.append(href)

    # fallback
    if not links:
        for a in soup.select('a[href]'):
            href = a.get('href', '')
            if href.startswith('http'):
                links.append(href)

    return list(dict.fromkeys(links))

# 공고 상세 링크만 남기기
def keep_only_job_detail_links(urls, site):
    if site == 'saramin.co.kr':
        return [
            u for u in urls
            if 'saramin.co.kr' in u and 'rec_idx=' in u and '/zf_user/jobs' in u and 'view' in u
        ]
    if site == 'jobkorea.co.kr':
        return [u for u in urls if 'jobkorea.co.kr/Recruit/GI_Read/' in u]
    return urls

# URL -> 공고 고유키(ID) 만들기
def make_job_key(url):
    m = re.search(r'rec_idx=(\d+)', url)
    if m:
        return f'saramin_{m.group(1)}'

    m = re.search(r'/Recruit/GI_Read/(\d+)', url)
    if m:
        return f'jobkorea_{m.group(1)}'

    return None

def main():
    seen_keys = set()
    rows = []

    for c in companies:
        for s in sites:
            for st in starts:
                search_url = naver_site_search_url(c, s, start=st)

                try:
                    r = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
                    r.raise_for_status()
                    soup = BeautifulSoup(r.text, 'html.parser')

                    links = extract_naver_result_links(soup)
                    links = [u for u in links if s in u]             # 도메인 제한
                    links = keep_only_job_detail_links(links, s)     # 공고 상세만

                    # 새 공고만 rows에 추가
                    added = 0
                    for u in links:
                        key = make_job_key(u)
                        if not key:
                            continue
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        rows.append([c, s, st, search_url, u, key])
                        added += 1

                    print(f'  -> 후보 {len(links)}개 / 신규 저장 {added}개 / 누적 {len(rows)}개')

                except Exception as e:
                    print('  -> FAIL:', e)

                time.sleep(1.2)

    # 저장
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['company', 'site', 'start', 'naver_search_url', 'result_url', 'job_key'])
        w.writerows(rows)

    print('=== 완료 ===')
    print(f'saved: {len(rows)} urls -> {output_csv}')

if __name__ == '__main__':
    main()