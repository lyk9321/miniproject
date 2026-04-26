# 전문 서비스업 경력 세부 사항

import re
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib

# 설정
FILE_PATH = 'saramin_전문서비스_AI.csv'
COL_EXP = 'experience'

# 경력 숫자(최소 연차) 추출 함수
def extract_min_year(val: str):
    """
    입력 예:
      '경력 3~10년' -> 3
      '경력3-10년'  -> 3
      '경력 3년↑'   -> 3
      '경력 12년↑'  -> 10 (cap)
      '경력'        -> None (무시)
      '경력무관'    -> None (무시)
    """
    if not isinstance(val, str):
        return None

    t = val.strip()
    if not t:
        return None

    # 공백, 화살표 등 정리
    t = re.sub(r'\s+', '', t)
    t = t.replace('↑', '').replace('↓', '')

    # 경력무관, 신입 등 제외
    if '경력무관' in t or '무관' in t:
        return None
    if '신입' in t:
        return None

    # '경력' 글자 자체가 없으면 제외
    if '경력' not in t:
        return None

    # 경력 값에서 첫 번째 숫자를 연차로 사용 (경력3~10년 -> 3, 경력10년이상 -> 10)
    m = re.search(r'(\d+)', t)
    if not m:
        return None  # 숫자 없는 '경력'은 무시

    year = int(m.group(1))

    # 10년 이상은 10으로 캡
    if year >= 10:
        return 10
    if year <= 0:
        return None

    return year


# 로드, 집계
df = pd.read_csv(FILE_PATH, encoding='utf-8-sig')
if COL_EXP not in df.columns:
    raise KeyError(f'컬럼 "{COL_EXP}" 를 찾을 수 없습니다. 현재 컬럼: {list(df.columns)}')

years = df[COL_EXP].fillna('').astype(str).apply(extract_min_year)
years = years.dropna().astype(int)  # None 제거

# 1~10년 카테고리(없어도 0으로 유지)
counts = years.value_counts().reindex(range(1, 11), fill_value=0).sort_index()

print('경력(숫자 포함) 데이터 건수:', int(counts.sum()))
print(counts)


# 시각화
plt.figure(figsize=(10, 5))
plt.bar(counts.index, counts.values)

#plt.title('경력 최소 연차 분포')
plt.xlabel('최소 요구 경력(년)')
plt.ylabel('공고 수')

plt.xticks(range(1, 11))

# 막대 위 수치 라벨(선택)
for x, v in zip(counts.index, counts.values):
    plt.text(x, v, f'{v}', ha='center', va='bottom')

plt.tight_layout()
plt.show()
