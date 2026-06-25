from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.schedule import Schedule
from app.models.time_off_request import TimeOffRequest
from app.models.shift_type import ShiftType
from app.models.user import User
from app.services.schedule_service import upsert_schedule
from app.schemas.time_off_request import (
    TimeOffRequestCreate,
    TimeOffCreateResponse,
    TimeOffMyRequestItem,
    TimeOffCancelResponse,
    TimeOffAdminListItem,
    TimeOffProcessedResponse,
    TimeOffRequestApprove,
    TimeOffRequestReject,
)

router = APIRouter()

VALID_TYPES = {"OFF", "VAC"}


# ══════════════════════════════════════════════════════════════
# 직원 전용 API
# ══════════════════════════════════════════════════════════════

@router.post(
    "/requests",
    response_model=TimeOffCreateResponse,
    status_code=201,
    summary="휴무·휴가 신청",
)
def create_time_off_request(
    body: TimeOffRequestCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ── 유형 검증 ──────────────────────────────────────────────
    if body.type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 유형입니다")

    # ── 날짜 검증 ──────────────────────────────────────────────
    if body.end_date < body.start_date:
        raise HTTPException(status_code=400, detail="종료일은 시작일 이후여야 합니다")

    # ── 중복 신청 차단 ──────────────────────────────────────────
    duplicate = db.query(TimeOffRequest).filter(
        TimeOffRequest.requester_id == current_user.user_id,
        TimeOffRequest.status == "pending",
        TimeOffRequest.start_date <= body.end_date,
        TimeOffRequest.end_date >= body.start_date,
    ).first()

    if duplicate:
        raise HTTPException(
            status_code=400,
            detail="해당 날짜 범위에 이미 대기 중인 신청이 있습니다",
        )

    # ── 신청 저장 ──────────────────────────────────────────────
    new_request = TimeOffRequest(
        requester_id=current_user.user_id,
        type=body.type,
        start_date=body.start_date,
        end_date=body.end_date,
        reason=body.reason,
        status="pending",
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return new_request


@router.get(
    "/requests/me",
    response_model=List[TimeOffMyRequestItem],
    summary="내 요청 목록 조회",
)
def get_my_requests(
    status: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(TimeOffRequest).filter(
        TimeOffRequest.requester_id == current_user.user_id
    )

    if status:
        query = query.filter(TimeOffRequest.status == status)

    return query.order_by(TimeOffRequest.created_at.desc()).all()


@router.patch(
    "/requests/{request_id}/cancel",
    response_model=TimeOffCancelResponse,
    summary="요청 취소",
)
def cancel_request(
    request_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = db.query(TimeOffRequest).filter(
        TimeOffRequest.request_id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="신청을 찾을 수 없습니다")

    if request.requester_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="본인의 신청만 취소할 수 있습니다")

    if request.status != "pending":
        raise HTTPException(status_code=400, detail="대기 중인 요청만 취소할 수 있습니다")

    request.status = "canceled"
    request.canceled_by = current_user.user_id
    request.processed_at = datetime.now()

    db.commit()
    db.refresh(request)

    return request


# ══════════════════════════════════════════════════════════════
# 관리자 전용 API
# ══════════════════════════════════════════════════════════════

@router.get(
    "/admin/requests",
    response_model=List[TimeOffAdminListItem],
    summary="전체 요청 목록 조회 (관리자)",
)
def get_all_requests(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """관리자가 전체 직원의 휴무·휴가 신청을 조회합니다. status, type 필터 지원."""
    query = db.query(TimeOffRequest).join(
        User, TimeOffRequest.requester_id == User.user_id
    )

    if status:
        query = query.filter(TimeOffRequest.status == status)
    if type:
        query = query.filter(TimeOffRequest.type == type)

    requests = query.order_by(TimeOffRequest.created_at.desc()).all()

    # requester_name을 플랫 구조로 구성
    result = []
    for r in requests:
        result.append(TimeOffAdminListItem(
            request_id=r.request_id,
            requester_id=r.requester_id,
            requester_name=r.requester.name if r.requester else "",
            type=r.type,
            start_date=r.start_date,
            end_date=r.end_date,
            reason=r.reason,
            status=r.status,
            admin_comment=r.admin_comment,
            created_at=r.created_at,
            processed_at=r.processed_at,
        ))

    return result


@router.patch(
    "/admin/requests/{request_id}/approve",
    response_model=TimeOffProcessedResponse,
    summary="요청 승인 (관리자)",
)
def approve_request(
    request_id: int,
    body: TimeOffRequestApprove,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    관리자가 휴무·휴가 신청을 승인합니다.
    VAC 승인 시 start_date~end_date 각 날짜에 VAC 코드를 upsert합니다.
    """
    request = db.query(TimeOffRequest).filter(
        TimeOffRequest.request_id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="신청을 찾을 수 없습니다")

    if request.status != "pending":
        raise HTTPException(status_code=400, detail="이미 처리된 요청입니다")

    # ── VAC 승인 시: schedules 테이블에 VAC 코드 자동 배정 ─────
    if request.type == "VAC":
        vac_shift = db.query(ShiftType).filter(ShiftType.code == "VAC").first()

        if not vac_shift:
            raise HTTPException(status_code=500, detail="VAC 근무 유형을 찾을 수 없습니다")

        # is_locked=True 인 스케줄과 충돌 여부 검사
        locked_conflict = db.query(Schedule).filter(
            Schedule.user_id == request.requester_id,
            Schedule.work_date >= request.start_date,
            Schedule.work_date <= request.end_date,
            Schedule.is_locked == True,
        ).first()
        if locked_conflict:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"{locked_conflict.work_date} 날짜에 교대 협의 중인 시프트가 있어 "
                    "휴가 승인이 불가합니다"
                ),
            )

        current_date = request.start_date
        while current_date <= request.end_date:
            upsert_schedule(db, request.requester_id, current_date, vac_shift.shift_type_id)
            current_date += timedelta(days=1)

    request.status = "approved"
    request.admin_comment = body.admin_comment
    request.processed_at = datetime.now()

    db.commit()
    db.refresh(request)

    return request


@router.patch(
    "/admin/requests/{request_id}/reject",
    response_model=TimeOffProcessedResponse,
    summary="요청 반려 (관리자)",
)
def reject_request(
    request_id: int,
    body: TimeOffRequestReject,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    request = db.query(TimeOffRequest).filter(
        TimeOffRequest.request_id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="신청을 찾을 수 없습니다")

    if request.status != "pending":
        raise HTTPException(status_code=400, detail="이미 처리된 요청입니다")

    request.status = "rejected"
    request.admin_comment = body.admin_comment
    request.processed_at = datetime.now()

    db.commit()
    db.refresh(request)

    return request
