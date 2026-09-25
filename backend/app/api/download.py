from fastapi import APIRouter, HTTPException, status, Response, Depends
from typing import Dict, Any
from app.models.db_models import User
from app.api.auth import get_current_user
from app.services.pdf_generator import generate_pdf_report

router = APIRouter()

@router.post("/download-report", status_code=status.HTTP_200_OK)
def download_pdf_report(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Generates and downloads a clean, professional PDF summary document
    from the structured summary data.
    """
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report data payload cannot be empty."
        )

    try:
        pdf_bytes = generate_pdf_report(payload)
        filename = "medbrief_clinical_report.pdf"
        patient_name = payload.get("patient_information", {}).get("patient_name")
        if patient_name and patient_name.strip() and patient_name.lower() != "not mentioned":
            sanitized_name = "".join(c for c in patient_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
            if sanitized_name:
                filename = f"medbrief_{sanitized_name.lower()}_report.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF report document: {str(e)}"
        )
