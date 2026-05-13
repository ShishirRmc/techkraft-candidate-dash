from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="reviewer")  # reviewer | admin
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    scores = relationship("Score", back_populates="reviewer")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    role_applied = Column(String, nullable=False)
    status = Column(String, nullable=False, default="new")  # new | reviewing | interviewed | offered | rejected | archived
    skills = Column(String, nullable=True)  # comma-separated
    internal_notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime, nullable=True)  # soft delete

    scores = relationship("Score", back_populates="candidate")

    __table_args__ = (
        Index("ix_candidates_status", "status"),
        Index("ix_candidates_role_applied", "role_applied"),
    )


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    category = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="scores")
    reviewer = relationship("User", back_populates="scores")

    __table_args__ = (
        Index("ix_scores_candidate_id", "candidate_id"),
        CheckConstraint("score >= 1 AND score <= 5", name="ck_score_range"),
        UniqueConstraint("candidate_id", "category", "reviewer_id", name="uq_score_per_category_per_reviewer"),
    )
