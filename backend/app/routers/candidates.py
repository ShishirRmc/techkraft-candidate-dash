from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models import User
from app.schemas import (
    CandidateDetail,
    PaginatedCandidates,
    ScoreCreate,
    ScoreOut,
    StatsResponse,
    SummaryResponse,
    NotesUpdate,
)
from app.services.candidate_service import (
    list_candidates as svc_list_candidates,
    get_candidate_detail,
    get_stats as svc_get_stats,
    create_score as svc_create_score,
    delete_score as svc_delete_score,
    generate_summary as svc_generate_summary,
    update_notes as svc_update_notes,
    CandidateNotFoundError,
    DuplicateScoreError,
    ScoreNotFoundError,
)

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc_get_stats(db)


@router.get("", response_model=PaginatedCandidates)
def list_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, alias="status"),
    role: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc"),
):
    items, total = svc_list_candidates(
        db,
        status=status_filter,
        role=role,
        skill=skill,
        keyword=keyword,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return PaginatedCandidates(items=items, total=total, page=page, page_size=page_size)


@router.get("/{candidate_id}", response_model=CandidateDetail)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_candidate_detail(db, candidate_id, current_user)
    except CandidateNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")


@router.post("/{candidate_id}/scores", response_model=ScoreOut, status_code=status.HTTP_201_CREATED)
def create_score(
    candidate_id: int,
    body: ScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return svc_create_score(
            db,
            candidate_id=candidate_id,
            category=body.category,
            score=body.score,
            reviewer_id=current_user.id,
            note=body.note,
        )
    except CandidateNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    except DuplicateScoreError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already scored this candidate in this category.",
        )


@router.post("/{candidate_id}/summary", response_model=SummaryResponse)
async def generate_summary(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        summary = await svc_generate_summary(db, candidate_id)
    except CandidateNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return SummaryResponse(summary=summary)


@router.patch("/{candidate_id}/notes", response_model=CandidateDetail)
def update_internal_notes(
    candidate_id: int,
    body: NotesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        return svc_update_notes(db, candidate_id, body.internal_notes)
    except CandidateNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")


@router.delete("/{candidate_id}/scores/{score_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_score(
    candidate_id: int,
    score_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        svc_delete_score(db, candidate_id, score_id)
    except CandidateNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    except ScoreNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
