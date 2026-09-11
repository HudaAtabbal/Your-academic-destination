"""
Router: checkins — راجع قسم 4 بملف wijhatak_api_contract.md
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_account, require_role
from app.errors import AppError
from app.models import Account, ActivityType, AccountRole, College, Lecture
from app.routers.checkins import checkin_service
from app.routers.checkins.checkin_schema import (
    CheckinCountResponse,
    CheckinResponse,
    LectureCheckinRequest,
    UniqueCodeRequest,
)

router = APIRouter(prefix="/checkins", tags=["checkins"])


@router.post(
    "/campus-entry",
    response_model=CheckinResponse,
    status_code=201,
    dependencies=[Depends(require_role(AccountRole.students_admin))],
)
def campus_entry_checkin(
    payload: UniqueCodeRequest, db: Session = Depends(get_db)
) -> CheckinResponse:
    checkin, student_name = checkin_service.create_campus_entry_checkin(db, payload.unique_code)
    return CheckinResponse(
        checkin_id=checkin.id, student_name=student_name, checked_in_at=checkin.checked_in_at
    )


@router.post(
    "/lecture",
    response_model=CheckinResponse,
    status_code=201,
    dependencies=[Depends(require_role(AccountRole.gate_scanner))],
)
def lecture_checkin(
    payload: LectureCheckinRequest, db: Session = Depends(get_db)
) -> CheckinResponse:
    checkin, student_name = checkin_service.create_lecture_checkin(
        db, payload.unique_code, payload.lecture_name
    )
    return CheckinResponse(
        checkin_id=checkin.id,
        student_name=student_name,
        checked_in_at=checkin.checked_in_at,
        lecture_name=checkin.lecture_name,
    )


@router.post(
    "/tour",
    response_model=CheckinResponse,
    status_code=201,
)
def tour_checkin(
    payload: UniqueCodeRequest,
    db: Session = Depends(get_db),
    current_account: Account = Depends(require_role(AccountRole.college_staff)),
) -> CheckinResponse:
    # الكلية بتنجلب من حساب الموظف نفسه — مش من جسم الطلب (راجع قسم 4.3 بالعقد)
    if current_account.college is None:
        raise AppError(
            status_code=400,
            error_code="validation_error",
            message="حساب مسؤول الكلية هاد مش مربوط بأي كلية — راجعي الأدمن",
        )

    checkin, student_name = checkin_service.create_tour_checkin(
        db, payload.unique_code, current_account.college
    )
    return CheckinResponse(
        checkin_id=checkin.id,
        student_name=student_name,
        checked_in_at=checkin.checked_in_at,
        college=checkin.college,
    )


@router.post(
    "/consultation",
    response_model=CheckinResponse,
    status_code=201,
    dependencies=[Depends(require_role(AccountRole.college_staff))],
)
def consultation_checkin(
    payload: UniqueCodeRequest, db: Session = Depends(get_db)
) -> CheckinResponse:
    checkin, student_name = checkin_service.create_consultation_checkin(db, payload.unique_code)
    return CheckinResponse(
        checkin_id=checkin.id, student_name=student_name, checked_in_at=checkin.checked_in_at
    )


@router.get("/count/today", response_model=CheckinCountResponse)
def count_checkins_today(
    # الأعمدة أنواع enum — FastAPI بيرجّع 422 موحّد لأي قيمة غير صالحة
    # (بدل ValueError مسرّب كـ 500 يلي كان يكشف internals)
    activity_type: ActivityType,
    college: College | None = None,
    lecture_name: Lecture | None = None,
    db: Session = Depends(get_db),
    # أي حساب فريق عمل مسجّل دخول يقدر يشوف العداد — مش محصور بدور معيّن،
    # لأنه مستخدم من أكتر من شاشة بأدوار مختلفة (بوابة، باب كلية، مدرج، لوحة المدير)
    current_account: Account = Depends(get_current_account),
) -> CheckinCountResponse:
    count = checkin_service.count_checkins_today(
        db, activity_type, college=college, lecture_name=lecture_name
    )
    return CheckinCountResponse(count=count)