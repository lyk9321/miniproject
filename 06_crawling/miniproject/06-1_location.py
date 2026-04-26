# 전문 서비스업 회사 위치 (세로막대그래프)

import re
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib

# 설정
FILE_PATH = 'saramin_전문서비스_AI.csv'
COL_LOCATION = 'location'
TOP_N = 10

# 시/도 정규화 매핑
REGION_MAP = {
    '서울': '서울', '서울특별시': '서울',
    '경기': '경기', '경기도': '경기',
    '인천': '인천', '인천광역시': '인천',
    '부산': '부산', '부산광역시': '부산',
    '대구': '대구', '대구광역시': '대구',
    '광주': '광주', '광주광역시': '광주',
    '대전': '대전', '대전광역시': '대전',
    '울산': '울산', '울산광역시': '울산',
    '세종': '세종', '세종특별자치시': '세종',
    '강원': '강원', '강원도': '강원', '강원특별자치도': '강원',
    '충북': '충북', '충청북도': '충북',
    '충남': '충남', '충청남도': '충남',
    '전북': '전북', '전라북도': '전북', '전북특별자치도': '전북',
    '전남': '전남', '전라남도': '전남',
    '경북': '경북', '경상북도': '경북',
    '경남': '경남', '경상남도': '경남',
    '제주': '제주', '제주도': '제주', '제주특별자치도': '제주',
    '서울전체':'서울', '경기전체':'경기'
}

SPECIAL_MAP = {
    '전국': '전국',
    '재택': '재택',
    '원격': '원격',
    'remote': '원격',
    'Remote': '원격',
}

# 상위 지역(시/도) 추출 + 정규화
def normalize_top_region(loc: str) -> str:
    """
    '서울 성동구' -> '서울'
    '서울특별시 성동구' -> '서울'
    '경상북도 포항시' -> '경북'
    '제주특별자치도 제주시' -> '제주'
    """
    if not isinstance(loc, str):
        return ''
    t = loc.strip()
    if not t:
        return ''
    
    # 괄호/특수문자 제거, 공백 정리
    t = re.sub(r'[\(\)\[\]\{\}]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()

    first = t.split(' ')[0].strip()
    if not first:
        return ''

    # 특수 케이스(전국/원격 등)
    if first in SPECIAL_MAP:
        return SPECIAL_MAP[first]

    # 정규화 매핑
    if first in REGION_MAP:
        return REGION_MAP[first]
    
    # '서울시', '부산시' 같은 축약이 섞이면 처리
    first2 = re.sub(r'(특별시|광역시|특별자치시|특별자치도|도|시)$', '', first)
    if first2 in REGION_MAP:
        return REGION_MAP[first2]

    return first

# 로드, 집계
df = pd.read_csv(FILE_PATH, encoding='utf-8-sig')
if COL_LOCATION not in df.columns:
    raise KeyError(f'컬럼 "{COL_LOCATION}" 를 찾을 수 없습니다. 현재 컬럼: {list(df.columns)}')

regions = df[COL_LOCATION].fillna('').astype(str).apply(normalize_top_region)
regions = regions[regions != '']

counts = regions.value_counts().head(TOP_N)

# 큰 값이 왼쪽에 오도록 내림차순
counts_sorted = counts.sort_values(ascending=False)


# 시각화 (세로 막대그래프)
plt.figure(figsize=(10, 6))
plt.bar(counts_sorted.index, counts_sorted.values)
#plt.title(f'상위 {TOP_N}개 지역 분포')
plt.xlabel('지역(시/도)')
plt.ylabel('공고 수')

# 막대 위 수치 라벨
for x, v in enumerate(counts_sorted.values):
    plt.text(x, v, f'{v}', ha='center', va='bottom')

plt.xticks(fontsize=14)

plt.tight_layout()
plt.show()

print(counts_sorted)