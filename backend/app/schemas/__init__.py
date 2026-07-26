from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    nom: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    nom: str
    email: EmailStr
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ResumeOut(BaseModel):
    id: int
    filename: str
    texte_extrait: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class JobDescriptionIn(BaseModel):
    description: str = Field(min_length=20)


class JobDescriptionOut(BaseModel):
    id: int
    description: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AnalysisRequest(BaseModel):
    resume_id: int
    job_description: str = Field(min_length=20)


class AnalysisResult(BaseModel):
    id: int
    score: int
    score_skills: int
    score_keywords: int
    score_experience: int
    score_education: int
    matched_skills: list[str]
    missing_skills: list[str]
    recommendations: list[str]
    compatibility_level: str
    optimized_text: str | None = None
    resume_text: str
    job_description: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AnalysisSummary(BaseModel):
    id: int
    score: int
    compatibility_level: str
    matched_skills: list[str]
    missing_skills: list[str]
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_analyses: int
    average_score: float
    last_analyses: list[AnalysisSummary]
