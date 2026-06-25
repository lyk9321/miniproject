from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


# ──────────────────────────────────────────────────────────────
# 요청 스키마 — 클라이언트 → 서버
# ──────────────────────────────────────────────────────────────

class TimeOffRequestCreate(BaseModel):
    """POST /api/requests 요청 바디. 유형/날짜 검증은 라우터에서 처리."""
    type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None


class TimeOffRequestApprove(BaseModel):
    admin_comment: Optional[str] = None
    force_overwrite: bool = False


class TimeOffRequestReject(BaseModel):
    admin_comment: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# 응답 스키마 — 서버 → 클라이언트
# ──────────────────────────────────────────────────────────────

class TimeOffCreateResponse(BaseModel):
    """POST /api/requests 201 응답"""
    request_id: int
    requester_id: int
    type: str
    start_date: date
    end_date: date
    reason: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TimeOffMyRequestItem(BaseModel):
    """GET /api/requests/me 목록 아이템"""
    request_id: int
    type: str
    start_date: date
    end_date: date
    reason: Optional[str]
    status: str
    admin_comment: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TimeOffCancelResponse(BaseModel):
    """PATCH /api/requests/{id}/cancel 200 응답"""
    request_id: int
    status: str

    class Config:
        from_attributes = True


class TimeOffAdminListItem(BaseModel):
    """GET /api/admin/requests 목록 아이템 — requester_name 플랫 구조"""
    request_id: int
    requester_id: int
    requester_name: str
    type: str
    start_date: date
    end_date: date
    reason: Optional[str]
    status: str
    admin_comment: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TimeOffProcessedResponse(BaseModel):
    """PATCH /api/admin/requests/{id}/approve|reject 200 응답"""
    request_id: int
    status: str
    admin_comment: Optional[str]
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


# 관리자 API용 — 레거시 (교체 대상)
class RequesterInfo(BaseModel):
    user_id: int
    name: str

    class Config:
        from_attributes = True


class TimeOffRequestResponse(BaseModel):
    """관리자 전용 API 응답 (신청자 정보 포함) — 레거시"""
    request_id: int
    type: str
    start_date: date
    end_date: date
    reason: Optional[str]
    status: str
    admin_comment: Optional[str]
    cancel_reason: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    requester: RequesterInfo

    class Config:
        from_attributes = True


class TimeOffRequestListResponse(BaseModel):
    data: List[TimeOffRequestResponse]


# ──────────────────────────────────────────────────────────────
# 관리자 대시보드 응답 스키마
# ──────────────────────────────────────────────────────────────

class WeeklyScheduleItem(BaseModel):
    date: str    # "YYYY-MM-DD"
    day: str     # "월"~"일"
    count: int   # is_work_day=True 직원 수


class AdminDashboardResponse(BaseModel):
    total_employees: int
    today_working: int
    today_on_leave: int
    pending_requests: int
    this_week_schedule: List[WeeklyScheduleItem]
