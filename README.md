# 이유경 · KDT AI·빅데이터 전문가 양성과정 12기 미니프로젝트 모음

> 6년 보건의료 경험을 가진 간호사 출신 데이터 분석가  
> 의료·헬스케어 도메인 지식과 데이터 분석·ML·웹 서비스 개발을 연결합니다

[![GitHub](https://img.shields.io/badge/GitHub-lyk9321-181717?logo=github)](https://github.com/lyk9321)
[![Blog](https://img.shields.io/badge/Blog-네이버블로그-03C75A?logo=naver)](https://blog.naver.com/lykces)
[![Email](https://img.shields.io/badge/Email-lyk9321@naver.com-EA4335?logo=gmail)](mailto:lyk9321@naver.com)

---

## 🗂️ 과정 개요

| 항목 | 내용 |
|------|------|
| 과정명 | KDT AI·빅데이터 전문가 양성과정 12기 (경북대학교) |
| 기간 | 2026.01 ~ 2026.06 |
| 주요 기술 | Python · Scikit-learn · Streamlit · FastAPI · React · MySQL · YOLO |

---

## ⭐ 대표 프로젝트

### 🏭 전기차 배터리 버스바 이상 탐지 AI 플랫폼 — 기업 프로젝트
> 팀 레포지토리 → **[KDT12-mnvision/KDT12-mnvison](https://github.com/KDT12-mnvision/KDT12-mnvison)**

비지도학습(OCC) 기반으로 전기차 배터리 버스바 리벳의 위치 이상·표면 결함을 통합 검출하고  
OK/NG 판정 및 현장 대응 UI까지 구현한 산업용 AI 비전 검사 솔루션

| 지표 | 결과 |
|------|------|
| AUROC | **0.994** (목표 0.95 초과) |
| F2 Score | **0.985** |
| FN | **4건** (CNN 대비 −89%) |
| 검사 시간 | **0.8초** (수초 → 0.8초 단축) |

**담당 역할:** 데이터 전처리 · 모델 개선 (ReConPatch 기반 단일 모델 통합 파이프라인 구축)  
`Python` `PyTorch` `OpenCV` `YOLO` `React`

---

### 🏥 건강위험 자가점검 서비스 — 헬스케어 AI
> 별도 레포지토리로 관리 중 → **[lyk9321/health-check-service](https://github.com/lyk9321/health-check-service)**

검진센터 임상 경험에서 출발한 프로젝트  
국민건강보험공단 **100만 건 실데이터**로 건강관리 유형을 6개로 분류하고 생활관리 방향을 추천

| 지표 | 결과 |
|------|------|
| Macro F1 | **0.9903** |
| 학습 데이터 | 국민건강보험공단 건강검진 100만 건 |
| 건강관리 유형 | 6개 (Rule Based 라벨링 기반) |
| 배포 | Streamlit Cloud 실서비스 운영 중 |

`Python` `Scikit-learn` `Random Forest` `Pandas` `NumPy` `Streamlit`

---

## 📁 미니프로젝트 목록

> 최신 프로젝트 순 정렬. 각 폴더 안의 README에서 상세 내용 확인 가능

### 🌐 웹·서비스 개발

| # | 프로젝트명 | 한 줄 설명 | 기술 스택 | 기간 |
|---|-----------|-----------|----------|------|
| 14 | 교대 근무 스케줄 관리 웹 애플리케이션 | 수기·Excel 근무표 관리의 비효율을 해소하기 위해 설계·구현한 교대 근무 스케줄 관리 웹 서비스 | `FastAPI` `React` `MySQL` `Docker` | 2026.04.27 ~ 05.04 |
| 12 | [KBO 원정 경기 플래너](./12_Web/) | 응원팀 입력 시 AI 승률 예측·날씨 리스크·맛집·숙소까지 제공하는 KBO 원정 팬 올인원 플래너 | `Streamlit` `Scikit-learn` `Selenium` | 2026.04.17 ~ 04.20 |
| 11 | [카카오톡 커스텀 이모티콘 생성기](./11_NLP/) | 사진 한 장으로 AI 이모티콘을 생성하고 GPT 챗봇과 주고받을 수 있는 웹 서비스 | `Streamlit` `OpenAI API` `Python` | 2026.04.09 ~ 04.13 |

### 🤖 딥러닝·컴퓨터 비전

| # | 프로젝트명 | 한 줄 설명 | 기술 스택 | 기간 |
|---|-----------|-----------|----------|------|
| 10 | [연기·불꽃 실시간 탐지를 통한 산불 조기 경보 시스템](./10_deep_learning/) | YOLOv8 경량화 전후 4개 모델의 탐지 성능을 정량 비교해 최적 배포 모델을 도출한 프로젝트 | `YOLO` `PyTorch` `Python` | 2026.03.31 ~ 04.02 |
| 09 | [헤이즐넛 이미지를 활용한 이상 탐지 및 결함 위치 시각화](./09_computer_vision_programming/) | HOG 특징 추출 + Isolation Forest로 이상 탐지 파이프라인을 구축하고 결함 위치를 시각화 | `Scikit-learn` `NumPy` `Matplotlib` | 2026.03.20 ~ 03.23 |

### 📊 데이터 분석·머신러닝

| # | 프로젝트명 | 한 줄 설명 | 기술 스택 | 기간 |
|---|-----------|-----------|----------|------|
| 08 | [노인을 위한 나라는 있다](./08_machine_learning/) | 증상·나이 기반 데이터로 뇌졸중 등 노인성 질환 위험을 예측하는 ML 분류 모델 구축 | `Scikit-learn` `XGBoost` `LightGBM` | 2026.03.09 ~ 03.16 |
| 07 | [혈액형과 MBTI는 과학인가 미신인가](./07_numpy/) | 자체 설문 데이터를 통계·ML로 분석해 MBTI가 성격을 예측하는 도구로 유효한지 검증 | `Scikit-learn` `Pandas` `Seaborn` | 2026.02.27 ~ 03.02 |
| 06 | [KDT 참여기업 업종별 채용 동향 분석](./06_crawling/) | 사람인·잡코리아 크롤링 데이터로 전문 서비스 분야의 실질적인 채용 구조와 요구 역량을 도출 | `Selenium` `BeautifulSoup` `KoNLPy` | 2026.02.20 ~ 02.23 |
| 05 | [빈집에 영향을 미치는 요소](./05_SQL/) | KOSIS 공공데이터를 MySQL로 구축해 고용 지표와 지역별 빈집 비율 간 상관관계를 분석 | `MySQL` `Pandas` `pymysql` | 2026.02.10 ~ 02.11 |
| 04 | [기후 변화가 사계절을 알리는 지표에 미치는 영향](./04_public_data/) | 공공 기후 데이터로 가을철 기온·강수량 변화와 단풍 시작 시기 간 상관관계를 탐색 | `Pandas` `Matplotlib` `Seaborn` | 2026.02.03 ~ 02.04 |
| 03 | [2022 FIFA 월드컵 데이터 분석 — 승리 요인 도출](./03_visualization/) | 2022 카타르 월드컵 데이터를 포지션별로 분석해 우승팀 아르헨티나의 강점·약점을 수치로 도출 | `Pandas` `Matplotlib` `Seaborn` | 2026.01.27 ~ 01.28 |
| 02 | [서울특별시 연료별 자동차 등록현황과 대기오염 지표 분석](./02_data_analysis/) | 친환경차 보급 확대 곡선과 대기오염 하락 곡선의 상관성을 2018~2024 실데이터로 검증 | `Pandas` `Matplotlib` `Seaborn` | 2026.01.14 ~ 01.21 |

### 🐍 Python 프로그래밍

| # | 프로젝트명 | 한 줄 설명 | 기술 스택 | 기간 |
|---|-----------|-----------|----------|------|
| 13 | [한컴타자연습](./13_typing_game/) | 한컴타자연습을 모티브로 레벨별 난이도 조정과 특수 단어 메커니즘을 구현한 pygame 타자 게임 | `Python` `pygame` | 2026.04.24 ~ 04.27 |
| 01-2 | [축구 선수 이름 맞히기](./01_python_programming/) | 무작위 선수 사진 10문제를 출제하고 정답을 판별하는 tkinter 기반 GUI 퀴즈 프로그램 | `Python` `tkinter` | 2026.01.11 ~ 01.12 |
| 01-1 | [Travel Archive](./01_python_programming/) | 여행 사진을 키보드 이벤트로 탐색할 수 있는 tkinter 기반 포토 갤러리 프로그램 | `Python` `tkinter` | 2026.01.07 ~ 01.11 |

---

## 🛠️ 기술 스택 요약

**Data Analysis**  
`Python` `Pandas` `NumPy` `Matplotlib` `Seaborn` `Plotly`

**Machine Learning / DL**  
`Scikit-learn` `XGBoost` `LightGBM` `PyTorch` `YOLO`

**Web / Backend**  
`Streamlit` `FastAPI` `React` `MySQL` `Docker`

**Data Collection**  
`Selenium` `BeautifulSoup`

**NLP**  
`KoNLPy` `OpenAI API`

---

## 📬 Contact

| | |
|---|---|
| ✉️ Email | lyk9321@naver.com |
| 🐙 GitHub | [github.com/lyk9321](https://github.com/lyk9321) |
| 📝 Blog | [blog.naver.com/lykces](https://blog.naver.com/lykces) |
