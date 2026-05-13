"""Business logic for candidate operations."""

import asyncio
from typing import Optional

from sqlalchemy import asc, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Candidate, Score, User
from app.schemas import CandidateDetail, CandidateListItem, ScoreOut


class CandidateNotFoundError(Exception):
    pass


class DuplicateScoreError(Exception):
    pass


class ScoreNotFoundError(Exception):
    pass


def get_stats(db: Session) -> dict:
    """Return counts of non-deleted candidates grouped by status."""
    rows = (
        db.query(Candidate.status, func.count(Candidate.id))
        .filter(Candidate.deleted_at.is_(None))
        .group_by(Candidate.status)
        .all()
    )
    counts = {status: count for status, count in rows}
    total = sum(counts.values())
    return {
        "total": total,
        "new": counts.get("new", 0),
        "reviewing": counts.get("reviewing", 0),
        "interviewed": counts.get("interviewed", 0),
        "offered": counts.get("offered", 0),
        "rejected": counts.get("rejected", 0),
    }


def list_candidates(
    db: Session,
    *,
    status: Optional[str] = None,
    role: Optional[str] = None,
    skill: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
) -> tuple[list[CandidateListItem], int]:
    """Return (items, total) for paginated candidate listing with score stats."""
    query = db.query(Candidate).filter(Candidate.deleted_at.is_(None))

    # Safe: SQLAlchemy parameterizes ilike() values — no raw SQL injection risk here.
    if status:
        query = query.filter(Candidate.status == status)
    if role:
        query = query.filter(Candidate.role_applied.ilike(f"%{role}%"))
    if skill:
        query = query.filter(Candidate.skills.ilike(f"%{skill}%"))
    if keyword:
        query = query.filter(
            (Candidate.name.ilike(f"%{keyword}%"))
            | (Candidate.email.ilike(f"%{keyword}%"))
            | (Candidate.skills.ilike(f"%{keyword}%"))
        )

    total = query.count()

    # Sorting
    sort_columns = {
        "name": Candidate.name,
        "created_at": Candidate.created_at,
        "status": Candidate.status,
        "role_applied": Candidate.role_applied,
    }
    sort_col = sort_columns.get(sort_by, Candidate.created_at)
    order_fn = asc if sort_order == "asc" else desc

    items = (
        query.order_by(order_fn(sort_col))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Enrich with score stats in a single grouped query
    if items:
        candidate_ids = [c.id for c in items]
        score_stats = (
            db.query(
                Score.candidate_id,
                func.count(Score.id).label("count"),
                func.avg(Score.score).label("avg"),
            )
            .filter(Score.candidate_id.in_(candidate_ids))
            .group_by(Score.candidate_id)
            .all()
        )
        stats_map = {row.candidate_id: (row.count, float(row.avg)) for row in score_stats}
    else:
        stats_map = {}

    enriched = []
    for c in items:
        item = CandidateListItem.model_validate(c)
        if c.id in stats_map:
            item.score_count = stats_map[c.id][0]
            item.avg_score = round(stats_map[c.id][1], 1)
        enriched.append(item)

    return enriched, total


def get_candidate_detail(
    db: Session,
    candidate_id: int,
    current_user: User,
) -> CandidateDetail:
    """Get candidate with RBAC-scoped scores. Hides internal_notes from reviewers."""
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id, Candidate.deleted_at.is_(None))
        .first()
    )
    if not candidate:
        raise CandidateNotFoundError()

    # RBAC: reviewer sees only their own scores; admin sees all
    if current_user.role == "admin":
        scores = db.query(Score).filter(Score.candidate_id == candidate_id).all()
    else:
        scores = (
            db.query(Score)
            .filter(Score.candidate_id == candidate_id, Score.reviewer_id == current_user.id)
            .all()
        )

    result = CandidateDetail.model_validate(candidate)

    if current_user.role == "admin":
        score_outs = []
        for s in scores:
            so = ScoreOut.model_validate(s)
            reviewer = db.query(User).filter(User.id == s.reviewer_id).first()
            if reviewer:
                so.reviewer_email = reviewer.email
            score_outs.append(so)
        result.scores = score_outs
    else:
        result.scores = [ScoreOut.model_validate(s) for s in scores]

    if current_user.role != "admin":
        result.internal_notes = None

    return result


def create_score(
    db: Session,
    candidate_id: int,
    category: str,
    score: int,
    reviewer_id: int,
    note: Optional[str] = None,
) -> Score:
    """Create a score. Raises CandidateNotFoundError or DuplicateScoreError."""
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id, Candidate.deleted_at.is_(None))
        .first()
    )
    if not candidate:
        raise CandidateNotFoundError()

    new_score = Score(
        candidate_id=candidate_id,
        category=category,
        score=score,
        reviewer_id=reviewer_id,
        note=note,
    )
    db.add(new_score)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateScoreError()
    db.refresh(new_score)
    return new_score


async def generate_summary(db: Session, candidate_id: int) -> str:
    """Generate a fake AI summary with a 2s simulated delay."""
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id, Candidate.deleted_at.is_(None))
        .first()
    )
    if not candidate:
        raise CandidateNotFoundError()

    scores = db.query(Score).filter(Score.candidate_id == candidate_id).all()

    # Simulate LLM processing delay
    await asyncio.sleep(2)

    score_summary = ""
    if scores:
        avg = sum(s.score for s in scores) / len(scores)
        categories = set(s.category for s in scores)
        score_summary = (
            f" They have been evaluated across {len(categories)} "
            f"{'category' if len(categories) == 1 else 'categories'} "
            f"with an average score of {avg:.1f}/5."
        )
    else:
        avg = 0

    summary = (
        f"{candidate.name} applied for the {candidate.role_applied} position. "
        f"Current status: {candidate.status}. "
        f"Skills: {candidate.skills or 'Not specified'}."
        f"{score_summary} "
        f"Based on the available data, this candidate "
        f"{'shows strong potential and should advance to the next stage.' if scores and avg >= 4 else 'requires further evaluation before a decision can be made.'}"
    )

    return summary


def update_notes(
    db: Session,
    candidate_id: int,
    internal_notes: Optional[str],
) -> CandidateDetail:
    """Update internal notes (admin only). Returns full candidate detail."""
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id, Candidate.deleted_at.is_(None))
        .first()
    )
    if not candidate:
        raise CandidateNotFoundError()

    candidate.internal_notes = internal_notes
    db.commit()
    db.refresh(candidate)

    scores = db.query(Score).filter(Score.candidate_id == candidate_id).all()
    result = CandidateDetail.model_validate(candidate)
    result.scores = [ScoreOut.model_validate(s) for s in scores]
    return result


def delete_score(
    db: Session,
    candidate_id: int,
    score_id: int,
) -> None:
    """Delete a score. Raises CandidateNotFoundError or ScoreNotFoundError."""
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id, Candidate.deleted_at.is_(None))
        .first()
    )
    if not candidate:
        raise CandidateNotFoundError()

    score = (
        db.query(Score)
        .filter(Score.id == score_id, Score.candidate_id == candidate_id)
        .first()
    )
    if not score:
        raise ScoreNotFoundError()

    db.delete(score)
    db.commit()
