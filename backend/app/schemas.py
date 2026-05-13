"""Pydantic schemas for request/response models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Auth Schemas ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str


# --- Candidate Schemas ---

class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    score: int
    reviewer_id: int
    note: Optional[str] = None
    reviewer_email: Optional[str] = None
    created_at: datetime


class CandidateListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role_applied: str
    status: str
    skills: Optional[str] = None
    score_count: int = 0
    avg_score: Optional[float] = None
    created_at: datetime


class CandidateDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role_applied: str
    status: str
    skills: Optional[str] = None
    internal_notes: Optional[str] = None
    created_at: datetime
    scores: list[ScoreOut] = []


class PaginatedCandidates(BaseModel):
    items: list[CandidateListItem]
    total: int
    page: int
    page_size: int


class StatsResponse(BaseModel):
    total: int
    new: int
    reviewing: int
    interviewed: int
    offered: int
    rejected: int


class ScoreCreate(BaseModel):
    category: str
    score: int = Field(ge=1, le=5)
    note: Optional[str] = None


class SummaryResponse(BaseModel):
    summary: str


class NotesUpdate(BaseModel):
    internal_notes: Optional[str] = None
