"""
Router: survey — راجع قسم 5 بملف wijhatak_api_contract.md
عام بالكامل (بدون Authorization) — الطالب نفسه بيعبّيه مباشرة عبر unique_code.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import rate_limit_public_lookup
from app.routers.survey import survey_service
from app.routers.survey.survey_schema import (
    SurveyStatusResponse,
    SurveySubmitRequest,
    SurveySubmitResponse,
)

router = APIRouter(prefix="/survey", tags=["survey"])


@router.get(
    "/{unique_code}/status",
    response_model=SurveyStatusResponse,
    dependencies=[Depends(rate_limit_public_lookup)],
)
def survey_status(unique_code: str, db: Session = Depends(get_db)) -> SurveyStatusResponse:
    answered = survey_service.get_survey_status(db, unique_code)
    return SurveyStatusResponse(answered=answered)


@router.post(
    "/{unique_code}",
    response_model=SurveySubmitResponse,
    status_code=201,
    dependencies=[Depends(rate_limit_public_lookup)],
)
def submit_survey(
    unique_code: str, payload: SurveySubmitRequest, db: Session = Depends(get_db)
) -> SurveySubmitResponse:
    survey = survey_service.submit_survey(
        db, unique_code, payload.opinion_change, payload.preferred_major
    )
    return SurveySubmitResponse(answered_at=survey.answered_at)