# 전문 서비스업 고용 형태 분포

import re
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib

FILE_PATH = 'saramin_전문서비스_AI.csv'
COL_JOB_TYPE = 'job_type'

CATEGORIES = ['정규직', '계약직', '기간제', '프리랜서', '위촉직', '인턴직']

# 차트에서 내부 라벨 숨길 카테고리
HIDE_LABEL_CATS = {'기간제', '프리랜서', '위촉직', '인턴직'}
SHOW_BIG_CATS = {'정규직', '계약직'}

# 색상
COLOR_MAP = {
    '정규직': '#1f77b4',
    '계약직': '#ff7f0e',
    '기간제': '#2ca02c',
    '프리랜서': '#d62728',
    '위촉직': '#9467bd',
    '인턴직': '#8c564b',
}

DONUT_WIDTH = 0.5  # 도넛 두께 (작을수록 구멍 큼)

#문자열에 섞인 급여/연봉 정보 제거
def strip_salary(text: str) -> str:
    if not isinstance(text, str):
        return ''
    t = text
    cut_keywords = r'(연봉|월급|급여|시급|일급|주급|협의|만원|원|pay|salary)'
    t = re.split(cut_keywords, t, maxsplit=1)[0]
    t = re.sub(r'\(([^)]*(연봉|월급|급여|시급|일급|주급|협의|만원|원)[^)]*)\)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\b\d[\d,.\s]*\b', ' ', t)
    t = re.sub(r'[₩$€¥]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


# 복합 고용형태 분리
def split_job_types(text: str) -> list:
    if not text:
        return []
    parts = re.split(r'[\/,;|·∙•\+\&\s]+', text)
    return [p.strip() for p in parts if p.strip()]

# 토큰을 카테고리로 매핑
def normalize_to_category(token: str) -> str:
    if not token:
        return ''
    t = token.strip()

    if '정규' in t:
        return '정규직'
    if '계약' in t:
        return '계약직'
    if '기간' in t:
        return '기간제'
    if '프리' in t or 'freelance' in t.lower():
        return '프리랜서'
    if '위촉' in t:
        return '위촉직'
    if '인턴' in t:
        return '인턴직'
    return ''

# raw job_type -> 카테고리 리스트(중복 제거)
def extract_categories(job_type_value: str) -> list:
    cleaned = strip_salary(job_type_value)
    tokens = split_job_types(cleaned)

    cats = []
    for tok in tokens:
        c = normalize_to_category(tok)
        if c:
            cats.append(c)

    # 한 공고 내 중복 카테고리 제거
    return list(dict.fromkeys(cats))


# 데이터 로드, 가중치 분할 집계
df = pd.read_csv(FILE_PATH, encoding='utf-8-sig')
if COL_JOB_TYPE not in df.columns:
    raise KeyError(f'컬럼 "{COL_JOB_TYPE}" 를 찾을 수 없습니다. 현재 컬럼: {list(df.columns)}')

counts = {c: 0.0 for c in CATEGORIES}  # float(가중치)로 집계
total_rows = 0
unknown_rows = 0

for v in df[COL_JOB_TYPE].fillna(''):
    total_rows += 1
    cats = extract_categories(str(v))

    if not cats:
        unknown_rows += 1
        continue

    # 복합형이면 1/n로 분할해서 총합이 공고 수로 유지되게 함
    w = 1.0 / len(cats)
    for c in cats:
        counts[c] += w

analyzed_total = total_rows - unknown_rows  # 분모

# 파이차트 표시용(0인 항목 제외)
labels = [k for k, v in counts.items() if v > 0]
values = [counts[k] for k in labels]

# 비율(%) (분모는 analyzed_total)
percents = [v / analyzed_total * 100 for v in values]

colors = [COLOR_MAP.get(lab, '#7f7f7f') for lab in labels]

# 도넛 차트
plt.figure(figsize=(9, 9))

wedges, texts, autotexts = plt.pie(
    values,
    labels=None,
    autopct='%1.1f%%',
    startangle=90,
    counterclock=False,
    colors=colors,
    wedgeprops={'width': DONUT_WIDTH, 'edgecolor': 'white'}
)

# 조각별 라벨 커스텀
for i, lab in enumerate(labels):
    pct = percents[i]

    # 숨길 카테고리: 내부 라벨 제거
    if lab in HIDE_LABEL_CATS:
        autotexts[i].set_text('')
        continue

    # 정규직/계약직: 카테고리명+비율, 흰색, 차트 안쪽(중앙 쪽)으로 이동
    if lab in SHOW_BIG_CATS:
        autotexts[i].set_text(f'{lab}\n{pct:.1f}%')
        autotexts[i].set_fontweight('bold')
        autotexts[i].set_color('white')

        if lab == '정규직':
            autotexts[i].set_fontsize(20)
            pull = 1.2      #중앙으로 당기는 정도(작을수록 더 중앙)
        else:
            autotexts[i].set_fontsize(15)
            pull = 1.2

        # 현재 위치 벡터를 원점(0,0) 쪽으로 당김 -> 파이 내부로 이동
        x, y = autotexts[i].get_position()
        autotexts[i].set_position((x * pull, y * pull))

    else:
        # 그 외는 %만 표시
        autotexts[i].set_text(f'{pct:.1f}%')
        autotexts[i].set_fontsize(10)

# 중앙 텍스트: 분석 공고(= 미분류 제외 공고 수)
plt.text(0, 0.05, '분석 공고', ha='center', va='center', fontsize=14, color='gray')
plt.text(0, -0.08, f'{analyzed_total:,}건', ha='center', va='center', fontsize=22, fontweight='bold')

# 범례: 비율(%)로 표시
legend_labels = [f'{lab} ({pct:.1f}%)' for lab, pct in zip(labels, percents)]
plt.legend(
    wedges,
    legend_labels,
    title='고용형태 비율',
    loc='center left',
    bbox_to_anchor=(1.02, 0.5),
    frameon=False
)

#plt.title('고용 형태 분포')
plt.tight_layout()
plt.show()

# 확인용 출력
print(f'전체 행: {total_rows}, 미분류: {unknown_rows}, 분석대상: {analyzed_total}')
