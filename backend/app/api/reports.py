import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db_models import User, Report
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/reports", status_code=status.HTTP_200_OK)
def get_user_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns list of reports belonging to current user, sorted newest first.
    If user is_admin, returns all reports in system.
    """
    if current_user.is_admin:
        reports = db.query(Report).order_by(Report.created_at.desc()).all()
    else:
        reports = db.query(Report).filter(Report.user_id == current_user.id).order_by(Report.created_at.desc()).all()

    result = []
    for r in reports:
        summary_obj = None
        if r.structured_summary_json:
            try:
                summary_obj = json.loads(r.structured_summary_json)
            except Exception:
                summary_obj = None

        result.append({
            "id": r.id,
            "user_id": r.user_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "patient_name": r.patient_name or "N/A",
            "source_type": r.source_type,
            "word_count": r.word_count,
            "sentence_count": r.sentence_count,
            "extractive_summary": r.extractive_summary,
            "abstractive_summary": r.abstractive_summary,
            "structured_summary": summary_obj
        })

    return {
        "success": True,
        "count": len(result),
        "reports": result
    }


@router.get("/reports/{report_id}", status_code=status.HTTP_200_OK)
def get_report_by_id(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a single report by ID.
    Enforces per-user authorization: returns 403 Forbidden if report belongs to another user
    (unless current user is an admin).
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} was not found."
        )

    if report.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view this report."
        )

    summary_obj = None
    if report.structured_summary_json:
        try:
            summary_obj = json.loads(report.structured_summary_json)
        except Exception:
            summary_obj = None

    return {
        "success": True,
        "report": {
            "id": report.id,
            "user_id": report.user_id,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "patient_name": report.patient_name or "N/A",
            "source_type": report.source_type,
            "word_count": report.word_count,
            "sentence_count": report.sentence_count,
            "extractive_summary": report.extractive_summary,
            "abstractive_summary": report.abstractive_summary,
            "structured_summary": summary_obj
        }
    }
