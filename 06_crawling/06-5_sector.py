# 전문 서비스업 직무, 기술, 도메인 - 워드클라우드, 막대그래프(Top10)

import re
import os
import random
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
from collections import Counter
from wordcloud import WordCloud


# 설정
CSV_FILE = 'saramin_전문서비스_AI.csv'
SECTOR_COL_CANDIDATES = ['sectors', 'sector', 'sector_tags']

OUTPUT_DIR = './output_sectors/'
SAVE_FIG = False  # True면 PNG 저장, False면 화면 출력만

TOP_N = 10
WC_MAX_WORDS = 120


# WordCloud 폰트 찾기
def find_korean_font() -> str:
    import matplotlib.font_manager as fm

    fixed_paths = [
        'C:/Windows/Fonts/malgun.ttf',
        'C:/Windows/Fonts/malgunbd.ttf',
        'C:/Windows/Fonts/NanumGothic.ttf',
        '/Library/Fonts/AppleGothic.ttf',
        '/System/Library/Fonts/AppleSDGothicNeo.ttc',
        '/Library/Fonts/NanumGothic.ttf',
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/nanum/NanumGothic.ttf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
    ]
    for p in fixed_paths:
        if os.path.exists(p):
            return p

    keywords = ('nanum', 'malgun', 'gothic', 'apple sd', 'noto sans cjk', 'dotum', 'gulim')
    for font in fm.fontManager.ttflist:
        if os.path.exists(font.fname) and any(k in font.name.lower() for k in keywords):
            return font.fname
    return ''


WC_FONT = find_korean_font()
if WC_FONT:
    print(f'[폰트] WordCloud: {WC_FONT}')
else:
    print('[경고] WordCloud 한글 폰트를 찾지 못했습니다. (한글 깨질 수 있음)')


# 태그 분류
TECH_TAGS = {
    'Python','Java','C++','C#','C언어','Javascript','TypeScript','Kotlin','Swift','PHP','HTML','HTML5','CSS','CSS3',
    'ECMAScript','Vue.js','VisualC·C++','Pro-C','ABAP','.NET','ASP.NET','VB.NET',
    'React','React-Native','ReactJS','Angular','Node.js','Spring','SpringBoot','Django','Flask','jQuery','Bootstrap',
    'Redux','Tailwind','JSP','WPF','MFC','Qt',
    'Pytorch','Tensorflow','Keras','Pandas','Numpy','Scikit-learn','CUDA','NVIDIA','OpenCV','DataMining','Deeplearning',
    'Matlab','LabVIEW','LLM',
    'AWS','Azure','GCP','Linux','Windows','Unix','CentOS','Ubuntu','redhat','AIX','Docker','Kubernetes','Jenkins','Git',
    'DevOps','MLOps','VMware','IDC','Apache','VPN','VDI','DRM',
    'SQL','MySQL','MSSQL','Oracle','OracleDB','PostgreSQL','MongoDB','MariaDB','RDBMS','DBMS','NoSQL','DW','ETL','DBA',
    'Figma','Sketch','Zeplin','XD','AutoCAD','CAD','PhotoShop','PowerPoint','GIS','ArcGIS','Splunk','SAP','ERP','API',
    'RestAPI','JPA','FPGA','RTOS','MCU','Flutter','IoT','OCR','GUI','BIM','EDA',
    'ISMS','ISMP','SWTEST','SWTESTING','SQA','ISTQB','ITQA','VoIP','MES','QMS','LMS','H/W','S/W',
}

JOB_TAGS = {
    '소프트웨어개발','백엔드/서버개발','웹개발','SE(시스템엔지니어)','프론트엔드','앱개발','SI개발','임베디드','펌웨어','풀스택',
    '앱기획','웹기획','서비스기획','PM(프로젝트매니저)','PL(프로젝트리더)','PO(프로덕트오너)','개발PM','PMO','퍼블리셔',
    '크로스플랫폼','알고리즘개발','로봇엔지니어','ML엔지니어','MLOps엔지니어','자동제어','전자제어','회로설계',
    'AI(인공지능)','머신러닝','딥러닝','데이터엔지니어','데이터분석가','데이터 사이언티스트','데이터분석','데이터시각화','빅데이터',
    'NLP(자연어처리)','음성인식','영상처리','이미지프로세싱','자율주행','컴퓨터비전','알고리즘','BI 엔지니어',
    '인프라','클라우드','네트워크','정보보안','보안컨설팅','기술지원','유지보수','IT컨설팅','아키텍쳐','시스템관리',
    '취약점진단','보안관제','모의해킹','악성코드','네트워크보안',
    'QA/테스터','QA','QC','SQA',
    '사업기획','마케팅기획','콘텐츠기획','경영기획','전략기획','신사업기획','기술기획','재무기획','상품기획','R&D기획',
    '사업관리','사업개발','경영분석','경영지원',
    '마케팅','마케팅전략','디지털마케팅','온라인마케팅','SNS마케팅','브랜드마케팅','콘텐츠마케팅','광고마케팅','퍼포먼스마케팅',
    'SEO','검색광고','영업관리','영업지원','영업전략','기술영업','솔루션기술영업','IT영업','시스템영업','B2B','B2C','B2G',
    'CRM','VOC분석','영업','공공영업','광고기획','AE(광고기획자)','미디어플래너',
    'UI/UX디자인','UI/UX','웹디자인','그래픽디자인','영상제작','영상편집','모션그래픽','시각디자인','브랜드디자인','BX디자인',
    '콘텐츠기획','콘텐츠에디터',
    '회계','재무','재무회계','관리회계','자금관리','IR/공시','세무회계','경리','재무분석',
    'HRD','HRM','인사교육','인사기획','조직문화','채용담당자',
    '교육기획','교육운영',
    '고객관리','CS','상담원',
    '물류관리','구매관리','SCM',
    '총무','사무직','사무보조','사무행정','문서작성','홍보',
    'R&D','연구원','기술연구','기계설계','품질관리','반도체','임상시험',
}

DOMAIN_TAGS = {
    'SI·시스템통합','솔루션','솔루션업체','정보통신','통신','SaaS','이커머스','전자상거래','쇼핑몰',
    '정보보안','방화벽','보안','VPN',
    '반도체','임베디드','전자','기계','제조','H/W','로봇','자율주행','IoT','의료기기',
    '제약/바이오','바이오','의약·제약','헬스케어','의료·보건','임상시험','생명과학',
    '금융기관','핀테크','보험','자산운용',
    '유통업','물류업',
    '광고기획사','광고대행사','게임','출판사','뉴미디어',
    '교육기관','인터넷교육',
    '회계법인','법률사무소','특허사무소','서치펌','컨설팅','헤드헌팅',
    '병원','대학교','부동산','건축','환경','에너지관리',
}


# 워드클라우드 컬러 팔레트
COLOR_PALETTES = {
    'job': [
        '#1f77b4', '#2196F3', '#0288D1', '#00897B', '#43A047',
        '#7B1FA2', '#C62828', '#E65100', '#F57F17', '#1565C0',
        '#00695C', '#4527A0', '#AD1457', '#558B2F', '#00838F',
    ],
    'tech': [
        '#E65100', '#F57C00', '#FF8F00', '#6A1B9A', '#283593',
        '#00695C', '#AD1457', '#1B5E20', '#0D47A1', '#880E4F',
        '#BF360C', '#827717', '#33691E', '#006064', '#4A148C',
    ],
    'domain': [
        '#2E7D32', '#00695C', '#1565C0', '#6A1B9A', '#AD1457',
        '#E65100', '#F57F17', '#4527A0', '#C62828', '#00838F',
        '#558B2F', '#0277BD', '#7B1FA2', '#00796B', '#1976D2',
    ],
}


# 태그 파싱
def clean_and_split(raw: str) -> list:
    if not isinstance(raw, str):
        return []

    # 날짜 제거
    cleaned = re.sub(r'(수정일|등록일)\s*\d{2}/\d{2}/\d{2}', '', raw)

    # '외' 제거
    cleaned = re.sub(r',?\s*외\s*', '', cleaned)

    # 쉼표 split (,, 처리 포함)
    parts = [p.strip() for p in cleaned.split(',')]

    tags = []
    for p in parts:
        p = p.strip().strip(',')
        if p and len(p) > 1:
            tags.append(p)

    # 중복 제거
    return list(dict.fromkeys(tags))


def load_counters(csv_path: str, sector_col: str):
    job_counter = Counter()
    tech_counter = Counter()
    domain_counter = Counter()
    other_counter = Counter()

    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    for raw in df[sector_col].fillna(''):
        for tag in clean_and_split(raw):
            # 우선순위 분류(중복 카운트 방지)
            if tag in JOB_TAGS:
                job_counter[tag] += 1
            elif tag in TECH_TAGS:
                tech_counter[tag] += 1
            elif tag in DOMAIN_TAGS:
                domain_counter[tag] += 1
            else:
                other_counter[tag] += 1

    return job_counter, tech_counter, domain_counter, other_counter


# 시각화
# 워드 클라우드
def draw_wordcloud(counter: Counter, category: str, title: str, save_name: str):
    if not counter:
        print(f'[WARN] {title}: 데이터 없음')
        return

    palette = COLOR_PALETTES.get(category, ['#1f77b4'])

    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        return random.choice(palette)

    wc = WordCloud(
        font_path=WC_FONT if WC_FONT else None,
        width=900,
        height=600,
        background_color='white',
        max_words=WC_MAX_WORDS,
        collocations=False,
        color_func=color_func,
        random_state=42,
        repeat=True
    ).generate_from_frequencies(dict(counter))

    plt.figure(figsize=(12, 8))
    plt.imshow(wc)
    plt.axis('off')
    plt.title(title)
    plt.tight_layout()
    plt.show()

# 막대그래프
def draw_top10_bar(counter: Counter, title: str, save_name: str, top_n: int = 10):
    top = counter.most_common(top_n)
    if not top:
        print(f'[WARN] {title}: 데이터 없음')
        return

    labels = [x[0] for x in top]   # 1위→10위 (왼쪽 -> 오른쪽)
    values = [x[1] for x in top]

    plt.figure(figsize=(11, 6))
    plt.bar(labels, values)
    plt.title(title)
    #plt.xlabel('Tag')
    plt.ylabel('Count')

    # x축 라벨 겹치면 회전
    plt.xticks(rotation=25, ha='right')

    # 막대 위 값 라벨
    max_v = max(values) if values else 0
    for x, v in enumerate(values):
        plt.text(x, v + max_v * 0.01, f'{v}', ha='center', va='bottom')

    plt.tight_layout()
    plt.show()

# 메인 함수
def main():
    df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
    sector_col = None
    for c in SECTOR_COL_CANDIDATES:
        if c in df.columns:
            sector_col = c
            break
    if sector_col is None:
        raise KeyError(f'sectors 컬럼을 찾을 수 없습니다. 후보={SECTOR_COL_CANDIDATES}, 실제={list(df.columns)}')

    job_cnt, tech_cnt, domain_cnt, other_cnt = load_counters(CSV_FILE, sector_col)

    print('[집계]')
    print(f'  직무   : 고유 {len(job_cnt)} / 총 {sum(job_cnt.values()):,}')
    print(f'  기술   : 고유 {len(tech_cnt)} / 총 {sum(tech_cnt.values()):,}')
    print(f'  도메인 : 고유 {len(domain_cnt)} / 총 {sum(domain_cnt.values()):,}')
    print(f'  기타   : 고유 {len(other_cnt)} / 총 {sum(other_cnt.values()):,} (참고)')

    draw_wordcloud(job_cnt, 'job', '', 'sectors_job_wordcloud.png')     # 직무
    draw_wordcloud(tech_cnt, 'tech', '', 'sectors_tech_wordcloud.png')  # 기술
    draw_wordcloud(domain_cnt, 'domain', '', 'sectors_domain_wordcloud.png') # 도메인 

    draw_top10_bar(job_cnt, '', 'sectors_job_top10.png', TOP_N)   # 직무
    draw_top10_bar(tech_cnt, '', 'sectors_tech_top10.png', TOP_N) # 기술
    draw_top10_bar(domain_cnt, '', 'sectors_domain_top10.png', TOP_N) # 도메인 


if __name__ == '__main__':
    main()
