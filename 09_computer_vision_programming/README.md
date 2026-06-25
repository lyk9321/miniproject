# 09. 헤이즐넛 이미지를 활용한 이상 탐지 및 결함 위치 시각화

> HOG 특징 추출 + Isolation Forest로 이상 탐지 파이프라인을 구축하고 결함 위치를 시각화한 컴퓨터 비전 프로젝트

`Python` `NumPy` `Scikit-learn` `scikit-image` `OpenCV` `Matplotlib` | 2026.03.20 ~ 03.23 | 팀 프로젝트  
**담당:** HOG 기법 파트 (특징 추출 · 모델 학습 · threshold 탐색 · 이상 위치 시각화)

### 프로젝트 구조

팀원 4명이 색상 히스토그램 / HOG / LBP / HOG+LBP 결합을 각각 담당, 동일한 Isolation Forest 모델로 특징 추출 방식별 성능을 비교 분석.

- **데이터:** MVTec AD hazelnut (학습: 정상 391장 / 테스트: 정상 40장 + 이상 70장)
- **이상 유형:** crack(균열) · cut(긁힘) · hole(구멍) · print(인쇄 자국)

### 파이프라인

```
이미지 128×128 리사이즈 → 그레이스케일 변환
→ HOG 특징 추출 (orientations=9, pixels_per_cell=16×16)
→ StandardScaler Z-score 정규화
→ Isolation Forest 학습 (n_estimators=500, 정상 이미지만)
→ Threshold 자동 탐색 (percentile 0~100, F1 기준)
→ 이상 판별 → absdiff + morphology + boundingRect 결함 위치 시각화
```

### 주요 결과

| 결함 유형 | 검출률(Recall) |
|----------|-------------|
| crack (균열) | **1.00** |
| cut (긁힘) | 0.94 |
| hole (구멍) | 0.84 |
| 정상 오탐 | 25/40건 (정상 recall 0.38) |

- **가설 부분 지지** — 형태 변화가 뚜렷한 결함(crack·cut)에는 HOG가 유효하게 작동
- 정상·이상 점수 분포가 크게 중첩되어 단독 판별 모델로는 신뢰하기 어려운 한계 확인
- 최종 threshold: percentile=65 → threshold=0.0621 (이상 70개 중 65개 검출)

### 트러블슈팅

**초기 threshold(percentile=5) 설정 시 anomaly recall 0.14에 불과**  
percentile 0~100 구간을 5 단위로 순회하며 F1 score 기준 최고점을 자동 탐색하는 방식으로 변경, percentile=65에서 anomaly recall 0.93 달성.

**StandardScaler 미적용 시 성능 저하**  
트리 기반 모델은 스케일 불변으로 알려져 있으나, Isolation Forest는 랜덤 분기 깊이 자체가 이상 점수에 영향을 주는 구조라 스케일이 큰 특징에 과도하게 의존하는 문제 발생. StandardScaler 적용 후 실제 성능 향상 확인.

**이상 위치 시각화 시 정상 부위도 박스로 잡히는 노이즈**  
이미지마다 촬영 각도·회전이 달라 단일 정상 참조 이미지와의 절대 차이 계산 시 회전 차이가 결함보다 크게 잡히는 경우 발생. morphology(OPEN→CLOSE) 연산으로 소규모 노이즈 제거, 참조 이미지를 정상 50장 평균으로 교체해 단일 이미지 의존성 완화.
