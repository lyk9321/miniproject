from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import date, timedelta

from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.models.time_off_request import TimeOffRequest
from app.models.swap_request import SwapRequest
from app.models.shift_type import ShiftType
from app.models.schedule import Schedule
from app.schemas.time_off_request import (
    AdminDashboardResponse,
    WeeklyScheduleItem,
)

router = APIRouter()

DAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"]


@router.get(
    "/admin/dashboard",
    response_model=AdminDashboardResponse,
    summary="관리자 대시보드",
)
def get_admin_dashboard(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    today = date.today()

    # ── 1. 전체 재직 직원 수 ───────────────────────────────────
    total_employees = db.query(func.count(User.user_id)).filter(
        User.is_active == True,
        User.role == "employee",
    ).scalar()

    # ── 2. 오늘 근무자 수 (COUNT DISTINCT user_id, is_work_day=True) ─
    today_working = (
        db.query(func.count(distinct(Schedule.user_id)))
        .join(ShiftType, Schedule.shift_type_id == ShiftType.shift_type_id)
        .filter(
            Schedule.work_date == today,
            ShiftType.is_work_day == True,
        )
        .scalar()
    )

    # ── 3. 오늘 휴가자 수 (COUNT DISTINCT user_id, VAC 코드) ───
    today_on_leave = (
        db.query(func.count(distinct(Schedule.user_id)))
        .join(ShiftType, Schedule.shift_type_id == ShiftType.shift_type_id)
        .filter(
            Schedule.work_date == today,
            ShiftType.code == "VAC",
        )
        .scalar()
    )

    # ── 4. 승인 대기 건수 합산 ─────────────────────────────────
    time_off_pending = db.query(func.count(TimeOffRequest.request_id)).filter(
        TimeOffRequest.status == "pending"
    ).scalar()

    swap_pending = db.query(func.count(SwapRequest.swap_request_id)).filter(
        SwapRequest.status.in_(["pending", "accepted"])
    ).scalar()

    pending_requests = time_off_pending + swap_pending

    # ── 5. 이번 주(월~일) 날짜별 근무자 수 ────────────────────
    # INTEGRATION.md 섹션 6: today.weekday() 기반 월요일 산출
    monday = today - timedelta(days=today.weekday())

    this_week_schedule = []
    for i in range(7):
        day = monday + timedelta(days=i)

        count = (
            db.query(func.count(distinct(Schedule.user_id)))
            .join(ShiftType, Schedule.shift_type_id == ShiftType.shift_type_id)
            .filter(
                Schedule.work_date == day,
                ShiftType.is_work_day == True,
            )
            .scalar()
        )

        this_week_schedule.append(
            WeeklyScheduleItem(
                date=day.strftime("%Y-%m-%d"),
                day=DAY_LABELS[i],
                count=count,
            )
        )

    return AdminDashboardResponse(
        total_employees=total_employees,
        today_working=today_working,
        today_on_leave=today_on_leave,
        pending_requests=pending_requests,
        this_week_schedule=this_week_schedule,
    )
