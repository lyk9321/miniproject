# 참여기업 채용 공고 분석: 워드클라우드, 막대그래프(키워드 Top10)

from konlpy.tag import Okt
from collections import Counter
from wordcloud import WordCloud
from collections import Counter
import platform
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import re
import koreanize_matplotlib


# 파일 경로 설정
TEXT_PATH = './참여기업 채용공고 크롤링.txt'
MASK_PATH = './cloud.png'

# 불용어(제외 단어) 설정: 항목 제목/라벨, 의미 없는 반복어, 공고 공통 단어 등
SECTION_STOPWORDS = {
    '담당업무', '자격요건', '우대사항', '사용스킬', '사용', '스킬', '기술스택',
    '지원자격', '필수요건', '필수사항', '우대', '요건', '업무', '자격', '사항',
    '경력', '신입', '학력', '무관', '가능', '이상', '이하',
    '경험', '능력', '사용', '기반', '관련', '유관', '해당', '분', '자', '등',
    '프로젝트', '경력직', '신입사원', '모집', '채용', '공고', '대한', '있다',
    '담당', '필수', '다양하다'
}

# 단어 길이가 너무 짧은 것(한 글자)은 노이즈가 많으므로 제거
MIN_TOKEN_LEN = 2

# 텍스트 전처리: 제목 라인/특수문자/불필요 기호 제거, 단어 분석이 잘 되도록 한글/영문/숫자/공백만 남김
def preprocess_text(raw: str) -> str:
    # 흔한 구분선, 기호 제거
    raw = raw.replace('\u00a0', ' ')
    raw = re.sub(r'[•·■◆▶➤▪️ㆍ]+', ' ', raw)
    raw = re.sub(r'[\(\)\[\]\{\}<>]+', ' ', raw)
    raw = re.sub(r'[/,:;|\\]+', ' ', raw)
    raw = re.sub(r'[-_=~`]+', ' ', raw)

    # '담당업무:' 같은 라벨 제거(콜론 포함 케이스)
    raw = re.sub(r'(담당업무|자격요건|우대사항|사용스킬|지원자격|필수요건|필수사항)\s*[:：]', ' ', raw)

    # 한글/영문/숫자/공백만 남김 (나머지 제거)
    raw = re.sub(r'[^0-9A-Za-z가-힣\s]', ' ', raw)

    # 공백 정리
    raw = re.sub(r'\s+', ' ', raw).strip()
    return raw

# 형태소 분석 → 명사/형용사만 추출
def extract_nouns_adjs(text: str) -> list:
    okt = Okt()
    # norm/stem 옵션으로 표준화/어간 추출(형용사 활용 변형 줄임)
    tagged = okt.pos(text, norm=True, stem=True)

    tokens = []
    for word, tag in tagged:
        if tag in ['Noun', 'Adjective']:
            if len(word) >= MIN_TOKEN_LEN:
                tokens.append(word)
    return tokens

# WordCloud 생성
def make_visual(tokens: list, stopwords: set, top_n: int = 80):
    # 빈도 계산
    counts = Counter(tokens)

    # 불용어 제거
    for sw in list(stopwords):
        if sw in counts:
            counts.pop(sw)

    # 상위 N개
    tags = counts.most_common(top_n)
    freq_dict = dict(tags)

    # 폰트 설정(윈도우/맥/리눅스)
    if platform.system() == 'Windows':
        font_path = r'c:\Windows\Fonts\malgun.ttf'
    elif platform.system() == 'Darwin':
        font_path = r'/System/Library/Fonts/AppleGothic'
    else:
        font_path = r'/usr/share/fonts/truetype/name/NanumMyeongjo.ttf'

    # 마스크
    mask = None
    try:
        mask = np.array(Image.open(MASK_PATH))
    except Exception:
        mask = None

    wc = WordCloud(
        font_path=font_path,
        width=900,
        height=650,
        background_color='white',
        max_font_size=180,
        repeat=True,
        colormap='tab10',
        mask=mask
    )

    cloud = wc.generate_from_frequencies(freq_dict)

    plt.figure(figsize=(12, 9))
    plt.axis('off')
    plt.imshow(cloud)
    plt.show()

    # tokens -> 빈도 계산
    counts = Counter(tokens)

    # 불용어 제거 (네 코드의 stopwords 사용)
    for sw in stopwords:
        counts.pop(sw, None)

    # Top10 추출
    top10 = counts.most_common(10)

    # 표로 확인
    df_top10 = pd.DataFrame(top10, columns=['word', 'count'])
    print(df_top10)

    # Top10 막대그래프
    words = [w for w, c in top10]
    freqs = [c for w, c in top10]

    plt.figure(figsize=(10, 5))
    plt.bar(words, freqs)
    plt.xticks(rotation=45, ha='right', fontsize=13)
    #plt.title('')
    #plt.xlabel('단어')
    plt.ylabel('빈도')
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    raw = open(TEXT_PATH, encoding='utf-8').read()
    cleaned = preprocess_text(raw)

    tokens = extract_nouns_adjs(cleaned)

    # (선택) 사용자/회사명/기술스택 등 특정 단어를 더 빼고 싶으면 여기에 추가
    custom_stopwords = set()  # 예: {'Python', 'Docker', 'Linux'} 등
    stopwords = SECTION_STOPWORDS | custom_stopwords

    make_visual(tokens, stopwords, top_n=80)
