import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.services.optimizer_service import optimize_sections
from app.config import settings
from app.core.deps import get_current_user, get_optional_user
from app.database import get_db
from app.models import Analysis, JobDescription, Resume, User
from app.schemas import AnalysisRequest, AnalysisResult, AnalysisSummary, DashboardStats, ResumeOut
from app.services.ats_engine import build_recommendations, compatibility_level, compute_ats_score
from app.services.file_parser import clean_text, extract_text, flatten_text
from app.services.generator_service import generate_docx, generate_pdf
from app.services.template_modifier_service import modify_resume_preserving_template
from app.services.optimizer_service import optimize_resume

router = APIRouter(prefix="/api", tags=["core"])


def _validate_upload(file: UploadFile) -> None:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")


@router.post("/resumes/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    _validate_upload(file)
    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_size_mb} MB")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "resume.pdf").suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    filepath = upload_dir / stored_name
    filepath.write_bytes(content)

    try:
        raw_text = extract_text(filepath)
    except Exception as exc:
        filepath.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Unable to read file: {exc}") from exc

    text = clean_text(raw_text)
    if not text:
        filepath.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="No text could be extracted from the file")

    resume = Resume(
        user_id=current_user.id if current_user else None,
        filename=file.filename or stored_name,
        filepath=str(filepath),
        texte_extrait=text,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/analysis/match", response_model=AnalysisResult)
def analyze_match(
    payload: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    resume = db.query(Resume).filter(Resume.id == payload.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    job = JobDescription(description=payload.job_description.strip())
    db.add(job)
    db.flush()

    scores = compute_ats_score(flatten_text(resume.texte_extrait), job.description)
    recommendations = build_recommendations(
        scores["matched_skills"], scores["missing_skills"], scores
    )
    optimized = optimize_resume(resume.texte_extrait, job.description)
    level = compatibility_level(scores["score"])

    analysis = Analysis(
        user_id=current_user.id if current_user else None,
        resume_id=resume.id,
        job_id=job.id,
        score=scores["score"],
        score_skills=scores["score_skills"],
        score_keywords=scores["score_keywords"],
        score_experience=scores["score_experience"],
        score_education=scores["score_education"],
        matched_skills=json.dumps(scores["matched_skills"]),
        missing_skills=json.dumps(scores["missing_skills"]),
        recommendations=json.dumps(recommendations),
        optimized_text=optimized,
        compatibility_level=level,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return AnalysisResult(
        id=analysis.id,
        score=analysis.score,
        score_skills=analysis.score_skills,
        score_keywords=analysis.score_keywords,
        score_experience=analysis.score_experience,
        score_education=analysis.score_education,
        matched_skills=scores["matched_skills"],
        missing_skills=scores["missing_skills"],
        recommendations=recommendations,
        compatibility_level=analysis.compatibility_level,
        optimized_text=optimized,
        resume_text=resume.texte_extrait,
        job_description=job.description,
        created_at=analysis.created_at,
    )


@router.get("/analysis/history", response_model=list[AnalysisSummary])
def history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analyses = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        AnalysisSummary(
            id=item.id,
            score=item.score,
            compatibility_level=item.compatibility_level,
            matched_skills=json.loads(item.matched_skills),
            missing_skills=json.loads(item.missing_skills),
            created_at=item.created_at,
        )
        for item in analyses
    ]


@router.get("/analysis/{analysis_id}", response_model=AnalysisResult)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis or analysis.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return AnalysisResult(
        id=analysis.id,
        score=analysis.score,
        score_skills=analysis.score_skills,
        score_keywords=analysis.score_keywords,
        score_experience=analysis.score_experience,
        score_education=analysis.score_education,
        matched_skills=json.loads(analysis.matched_skills),
        missing_skills=json.loads(analysis.missing_skills),
        recommendations=json.loads(analysis.recommendations),
        compatibility_level=analysis.compatibility_level,
        optimized_text=analysis.optimized_text,
        resume_text=analysis.resume.texte_extrait,
        job_description=analysis.job.description,
        created_at=analysis.created_at,
    )


@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analyses = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .all()
    )
    average = sum(a.score for a in analyses) / len(analyses) if analyses else 0.0
    last = analyses[:5]
    return DashboardStats(
        total_analyses=len(analyses),
        average_score=round(average, 1),
        last_analyses=[
            AnalysisSummary(
                id=item.id,
                score=item.score,
                compatibility_level=item.compatibility_level,
                matched_skills=json.loads(item.matched_skills),
                missing_skills=json.loads(item.missing_skills),
                created_at=item.created_at,
            )
            for item in last
        ],
    )


@router.get("/analysis/{analysis_id}/download/{fmt}")
def download_optimized(
    analysis_id: int,
    fmt: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if current_user and analysis.user_id and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if fmt not in {"pdf", "docx"}:
        raise HTTPException(status_code=400, detail="Format must be pdf or docx")

    export_dir = Path(settings.upload_dir) / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    output = export_dir / f"optimized_{analysis_id}.{fmt}"

    original_path = Path(analysis.resume.filepath)
    original_suffix = original_path.suffix.lower()
    resume_text = analysis.resume.texte_extrait
    job_text = analysis.job.description
    fallback_text = analysis.optimized_text or resume_text

  
    if fmt == "pdf":
        sections = optimize_sections(
            resume_text,
            job_text
        )

        generate_pdf(
            sections,
            output
        )


    elif fmt == original_suffix.lstrip("."):
        # DOCX -> DOCX : conserver le template original
        modify_resume_preserving_template(
            original_path,
            output,
            resume_text,
            job_text
        )


    else:
        # Génération DOCX simple
        generate_docx(
            fallback_text,
            output
        )


    if fmt == "pdf":
        media_type = "application/pdf"
    else:
        media_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )


    original_name = Path(analysis.resume.filename).stem
    download_name = f"{original_name}_optimise.{fmt}"


    return FileResponse(
        path=output,
        filename=download_name,
        media_type=media_type
    )