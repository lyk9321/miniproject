# 05. 빈집에 영향을 미치는 요소

> KOSIS 공공데이터를 MySQL로 구축하고, 지역별 고용 지표와 빈집 비율 간 상관관계를 분석한 프로젝트

`Python` `MySQL` `Pandas` `Matplotlib` `Seaborn` `pymysql` | 2026.02.10 ~ 02.11 | 팀 프로젝트  
**담당:** 고용 파트 (데이터 수집 · SQL 테이블 설계 및 JOIN 키 구성 · 분석 · 시각화 · 발표자료 제작)

### 분석 목표 및 가설

분석 기간: 2018~2024년 / 17개 시도 / 고용 지표 3종 (고용률·실업률·경제활동참가율)

- **가설 1** 고용률이 낮은 지역일수록 빈집 비율이 높을 것이다 (음의 상관관계)
- **가설 2** 실업률이 높은 지역일수록 빈집 비율이 높을 것이다 (양의 상관관계)
- **가설 3** 경제활동참가율이 낮은 지역일수록 빈집 비율이 높을 것이다 (음의 상관관계)

### DB 설계

MySQL `mini` 데이터베이스에 5개 테이블로 구성. 테이블 간 JOIN을 위해 `CONCAT(year, 지역코드)` 방식으로 연도+지역 복합 키(`region_id`)를 직접 설계하여 4개 테이블 INNER JOIN으로 통합 데이터프레임 생성.

```sql
SELECT emp.region, emp.year, emp.employment_rate,
       unemp.unemployment_rate, par.participation_rate, empty2.empty_rate
FROM employment_rate AS emp
    INNER JOIN unemployment_rate AS unemp ON emp.region_id = unemp.region_id
    INNER JOIN participation_rate AS par  ON unemp.region_id = par.region_id
    INNER JOIN empty2 ON par.region_id = empty2.region_id;
```

### 주요 결과

| 가설 | 상관계수 | 예상 방향 | 실제 결과 |
|------|---------|----------|---------|
| 빈집 × 고용률 | r = +0.55 | 음(−) | ❌ 기각 — 반대 방향 |
| 빈집 × 실업률 | r = −0.51 | 양(+) | ❌ 기각 — 반대 방향 |
| 빈집 × 경제활동참가율 | r = +0.52 | 음(−) | ❌ 기각 — 반대 방향 |

세 가설 모두 기각. 제주·충청 등 농촌형 지역이 관광·농업 특수 산업 구조로 인해 고용 지표가 높게 형성되어 있어 단순 상관분석만으로는 고용이 빈집 증가를 유발한다고 해석하기 어려움. 교란 변수 통제 및 복합 요인 분석 필요.

### 트러블슈팅

**지역명 불일치로 JOIN 결과 누락·중복 발생**  
테이블마다 `'제주도'` / `'제주특별자치도'` 표기가 혼용되어 JOIN 시 행 누락 발생.  
`UPDATE`로 지역명 통일 후, 문자열 대신 `CONCAT(year, 지역코드)`로 생성한 숫자 복합 키(`region_id`)로 JOIN을 수행하여 해결.
