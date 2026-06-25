# 14. 교대 근무 스케줄 관리 웹 애플리케이션 — ShiftMate

> 수기·Excel 근무표 관리의 비효율을 해소하기 위해 관리자·직원 역할을 분리하여 설계·구현한 교대 근무 스케줄 관리 웹 서비스

`Python` `FastAPI` `React` `MySQL` `Docker` | 2026.04.27 ~ 05.04 | 팀 프로젝트 (4인)  
**팀 레포지토리:** [shiftmate0/shiftmate](https://github.com/shiftmate0/shiftmate)  
**담당:** 휴무·휴가 신청 API · 관리자 대시보드 FE·BE · 요청 관리 화면 · 공통 레이아웃 · FE·BE 연동

### 담당 파일

```
backend/app/api/time_off_requests.py   ← 휴무·휴가 API 6개
backend/app/api/dashboard.py           ← 관리자 대시보드 API
backend/app/models/time_off_request.py ← DB 모델
backend/app/schemas/time_off_request.py← Pydantic 스키마 (요청/응답 분리)
frontend/src/pages/admin/DashboardPage.jsx    ← 관리자 대시보드 화면
frontend/src/pages/admin/RequestsPage.jsx     ← 요청 관리 화면 (관리자)
frontend/src/pages/employee/RequestsPage.jsx  ← 휴무·휴가 신청+내역 화면 (직원)
frontend/src/components/layout/AppLayout.jsx  ← 공통 사이드바·헤더 레이아웃
```

### 핵심 설계 판단

**요청 이력 무삭제 원칙** — 휴무·휴가·교대 요청은 승인/반려/취소 이후에도 DELETE 없이 이력으로 보존. 근무 기록은 분쟁 시 증빙 자료가 되므로 삭제하지 않는 것이 실무적으로 적합하다고 판단. 직원 계정은 소프트 삭제(`is_active=False`), 근무 유형은 미사용만 DELETE 허용으로 도메인별 삭제 정책을 다르게 설계.

**VAC 승인 시 스케줄 자동 upsert** — 휴가 승인 시 관리자가 별도로 근무표를 편집하는 수작업 없이 `start_date ~ end_date` 범위의 `schedules` 테이블에 VAC 코드 자동 배정. 단, `is_locked=True`인 날짜가 포함된 경우 충돌 방지를 위해 승인 차단 후 409 반환.

**대시보드 실시간 DB 집계** — KPI 수치를 매 요청마다 DB에서 직접 집계하여 반환. 근무표 변경·요청 처리 후 별도 동기화 없이 수치가 즉시 반영되는 실시간성이 하드코딩 방식보다 중요하다고 판단.

### 주요 결과

- 휴무·휴가 신청~승인~취소 전체 요청 주기를 6개 API로 완성, FastAPI Swagger 34개 엔드포인트 문서화 및 테스트 완료
- VAC 승인 1회로 `schedules` 테이블 자동 반영 — 관리자 별도 편집 불필요
- 관리자 대시보드: 오늘 근무자 수·휴가자 수·승인 대기 건수·이번 주 근무 차트를 단일 엔드포인트로 실시간 집계

### 트러블슈팅

**VAC 승인 시 교대 협의 중인 날짜 덮어쓰기 문제**  
초기 설계에서 `is_locked=True` 날짜 충돌 검사 로직이 누락되어 `upsert_schedule()` 호출 시 교대 협의 중인 스케줄을 덮어쓸 수 있었음.  
`upsert_schedule()` 호출 전에 `Schedule.is_locked == True`인 날짜가 신청 범위 내에 있는지 먼저 쿼리하고, 충돌 시 해당 날짜를 메시지에 포함한 409 에러를 반환하도록 처리. 충돌 검사 → upsert 실행 순서를 명확히 분리하여 스케줄 일관성 보장.

**대시보드 근무자 수 중복 집계 문제**  
`COUNT(Schedule.user_id)` 사용 시 같은 직원이 여러 스케줄 행에 중복으로 집계되어 실제 인원보다 수치가 높게 나옴.  
`func.count(distinct(Schedule.user_id))`로 변경하여 동일 직원 중복 제거. `today_on_leave` 집계에도 동일 방식 적용.

**빠른 승인 처리 후 KPI 수치가 갱신되지 않는 문제**  
요청 목록의 `recentRequests` 상태만 업데이트하고 대시보드 KPI 상태를 재조회하지 않은 것이 원인.  
`handleQuickApprove`, `handleQuickReject` 함수 내에 `fetchDashboard()`를 추가하여 처리 완료 후 전체 KPI 데이터를 서버에서 재조회하도록 수정.
