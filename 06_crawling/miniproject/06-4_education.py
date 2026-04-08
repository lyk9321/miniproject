# 전문 서비스업 학력 사항 분포

import re
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
import re
import pandas as pd
import matplotlib.pyplot as plt

# 설정
FILE_PATH = 'saramin_전문서비스_AI.csv'
COL_EDU = 'education'

CATEGORIES = ['고졸', '초대졸', '대졸', '석사', '박사', '학력무관']

# 파이 내부에 '카테고리명+비율'을 표시할 항목
SHOW_INSIDE_CATS = {'초대졸', '대졸', '학력무관'}

# 색상
COLOR_MAP = {
    '고졸': '#ff7f0e',
    '초대졸': '#2ca02c',
    '대졸': '#1f77b4',
    '석사': '#8c564b',
    '박사': '#d62728',
    '학력무관': '#9467bd'
}


# 학력 정규화 함수
def normalize_education(val: str) -> str:
    if not isinstance(val, str):
        return ''
    t = val.strip()
    if not t:
        return ''

    # ↑/↓ 및 부가어 제거
    t = t.replace('↑', '').replace('↓', '')
    t = re.sub(r'(이상|이하|가능|우대)', '', t)
    t = re.sub(r'\s+', '', t)

    if '학력무관' in t or '무관' in t:
        return '학력무관'
    if '박사' in t:
        return '박사'
    if '석사' in t:
        return '석사'
    if '초대졸' in t or '전문대' in t:
        return '초대졸'
    if '대졸' in t:
        return '대졸'
    if '고졸' in t:
        return '고졸'
    return ''


# 로드, 집계
df = pd.read_csv(FILE_PATH, encoding='utf-8-sig')

edu_norm = df[COL_EDU].fillna('').astype(str).apply(normalize_education)
edu_norm = edu_norm[edu_norm != '']

counts = edu_norm.value_counts()

labels = [cat for cat in CATEGORIES if counts.get(cat, 0) > 0]
values = [int(counts.get(cat, 0)) for cat in labels]

total = sum(values)
percents = [v / total * 100 for v in values]

# labels 순서대로 색 리스트 생성 (정의되지 않은 항목은 회색 처리)
colors = [COLOR_MAP.get(lab, '#7f7f7f') for lab in labels]

# 시각화 (파이차트)
plt.figure(figsize=(9, 9))

wedges, texts, autotexts = plt.pie(
    values,
    labels=None,          # 기본 라벨 숨김
    autopct='%1.1f%%',
    startangle=90,
    counterclock=False,
    colors=colors
)

# 파이 내부 라벨 커스터마이징
for i, lab in enumerate(labels):
    pct = percents[i]

    if lab in SHOW_INSIDE_CATS:
        autotexts[i].set_text(f'{lab}\n{pct:.1f}%')  # 카테고리명 + 비율
        autotexts[i].set_color('white')
        autotexts[i].set_fontweight('bold')
        autotexts[i].set_fontsize(16)
    else:
        autotexts[i].set_text('')  # 나머지는 파이 내부 라벨 숨김

# 범례: 나머지 카테고리만 '이름 (비율%)' 표시
legend_labels = [f'{lab} ({pct:.1f}%)' for lab, pct in zip(labels, percents)]
plt.legend(
    wedges,
    legend_labels,
    title='학력 비율',
    loc='center left',
    bbox_to_anchor=(1.02, 0.5),
    frameon=False,
    prop={'size': 12},
    title_fontsize=13
)

#plt.title('학력 분포')
plt.tight_layout()
plt.show()