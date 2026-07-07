# 08. 노인을 위한 나라는 있다 — 뇌졸중 위험 예측 ML 모델

> 나이·증상 기반 데이터로 뇌졸중 위험군을 분류하는 최적 머신러닝 모델을 선정하고 예측 근거를 시각화한 프로젝트

`Python` `Pandas` `NumPy` `Scikit-learn` `XGBoost` `LightGBM` `Matplotlib` | 2026.03.09 ~ 03.16 | 팀 프로젝트  
**담당:** 뇌졸중 파트 (데이터 수집 및 전처리 · EDA · 12개 분류 모델 훈련 및 평가 · 최종 모델 선정 및 해석 · 시각화)

### 분석 목표 및 가설

데이터: Kaggle Stroke Risk Prediction Dataset (70,000행 / 15개 증상 이진 피처 + Age → 65세 이상 약 25,000행 사용)

- **가설 1** 나이가 많을수록 뇌졸중 위험 비율이 높아질 것이다
- **가설 2** 보유 증상 수가 많을수록 뇌졸중 위험도가 높아질 것이다

### 모델 선정 과정

총 12개 모델에 동일한 3단계 파이프라인 적용: 기본 파라미터 훈련 + `cross_validate` 과적합 확인 → `GridSearchCV` 최적 하이퍼파라미터 탐색 → 5개 지표(Accuracy·Precision·Recall·F1·AUC)로 최종 평가

> Decision Tree / Random Forest / Extra Tree / GBM / HistGBM / XGBoost / XGBoost(Early Stopping) / LightGBM / LightGBM(Early Stopping) / Logistic Regression / Ridge(L2) / Lasso(L1)

**최종 후보 Random Forest vs XGBoost 심층 비교**

| 지표 | Random Forest | XGBoost |
|------|-------------|---------|
| Accuracy | 0.9748 | 0.9932 |
| Recall | 0.9843 | 0.9939 |
| AUC | 0.9909 | 0.9997 |
| 예측 확률 분포 | **0.5~1.0 구간에 걸쳐 분포** | 0.0 또는 1.0 극단값 집중 (95.4%) |

수치 지표는 XGBoost가 우세했으나, **의료 데이터에서는 위험/정상 이분법보다 위험 정도의 연속적 판단이 중요**하다는 판단 하에 예측 확률이 단계적으로 분포하는 **Random Forest를 최종 모델로 선정.**

### 주요 결과

- **가설 1 지지** — 연령대별 위험 비율: 30세 미만 18.9% → 45~64세 74.0% → 65세 이상 95.9%로 단조 증가. Age와 At Risk 상관계수 0.61로 전체 피처 중 최강
- **가설 2 지지** — 증상 1~2개 시 위험군 비율 ≈ 0%, 4개 이상부터 급격히 증가, 10개 이상 시 100% 도달
- **Feature Importance** — Age(0.2221)가 2위 Fatigue & Weakness(0.0671)의 3배 이상으로 압도적 1위

### 트러블슈팅

**타깃 변수 간 데이터 누수(Data Leakage)**  
`Stroke Risk(%)`와 `At Risk(Binary)` 간 상관계수 0.79로 `At Risk`가 `Stroke Risk` 50% 기준으로 정의된 종속 관계임을 히트맵 분석으로 확인. `Stroke Risk(%)`를 피처에서 제거하고 `At Risk(Binary)`만 타깃으로 사용해 누수 제거.

**65세 이상 필터링 후 클래스 불균형 극심 (위험군 95.4% / 정상군 4.6%)**  
단순 정확도로는 전부 위험군으로 예측해도 95% 이상이 나오는 구조. `class_weight='balanced'`를 지원 모델에 적용하고, XGBoost에는 `scale_pos_weight = (정상군 수 / 위험군 수)`를 직접 계산해 전달. 평가 지표도 Accuracy 단일 지표 대신 Precision·Recall·F1·AUC를 함께 확인하는 방식으로 전환.
