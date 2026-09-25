from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
from app.models.schemas import ExtractTextRequest, ExtractResponse
from app.models.db_models import User
from app.api.auth import get_current_user
from app.services.text_extraction import (
    extract_text_from_pdf,
    extract_text_from_plain_text,
    clean_extracted_text,
)
from app.services.ocr_extraction import ocr_image
from app.services.noise_filtering import strip_document_noise

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit
ALLOWED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


@router.post("/extract-pdf", response_model=ExtractResponse, status_code=status.HTTP_200_OK)
async def extract_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Extracts and cleans text from an uploaded PDF medical report file (text or scanned).
    """
    # 1. Validate file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files (.pdf) are accepted."
        )

    # 2. Read bytes & check size limit
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the maximum allowed limit of 10MB."
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded PDF file is empty."
        )

    # 3. Extract text from PDF (with OCR fallback for scanned PDFs)
    try:
        raw_text = extract_text_from_pdf(file_bytes)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read this PDF file: {str(e)}"
        )

    # 4. Filter boilerplate noise & clean text
    noise_stripped = strip_document_noise(raw_text)
    cleaned_text = clean_extracted_text(noise_stripped)

    # 5. Check if text is empty
    warning_msg = None
    if not cleaned_text:
        warning_msg = (
            "No extractable text found in PDF. The document may be blank or contain unreadable imagery."
        )

    word_count = len(cleaned_text.split()) if cleaned_text else 0
    char_count = len(cleaned_text)

    return ExtractResponse(
        success=True,
        extracted_text=cleaned_text,
        character_count=char_count,
        word_count=word_count,
        source_type="pdf",
        warning=warning_msg
    )


@router.post("/extract-image", response_model=ExtractResponse, status_code=status.HTTP_200_OK)
async def extract_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Extracts and cleans text from an uploaded medical image file (PNG/JPG/JPEG) via OpenCV + Tesseract OCR.
    """
    # 1. Validate file extension
    filename_lower = file.filename.lower()
    if not filename_lower.endswith(ALLOWED_IMAGE_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only image files (.png, .jpg, .jpeg) are accepted."
        )

    # 2. Read bytes & check size limit
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the maximum allowed limit of 10MB."
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty."
        )

    # 3. Perform OCR
    try:
        raw_text = ocr_image(file_bytes)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}"
        )

    # 4. Filter noise & clean text
    noise_stripped = strip_document_noise(raw_text)
    cleaned_text = clean_extracted_text(noise_stripped)

    warning_msg = None
    if not cleaned_text:
        warning_msg = (
            "No extractable text found in image. Please ensure the image is clear and legible."
        )

    word_count = len(cleaned_text.split()) if cleaned_text else 0
    char_count = len(cleaned_text)

    return ExtractResponse(
        success=True,
        extracted_text=cleaned_text,
        character_count=char_count,
        word_count=word_count,
        source_type="image",
        warning=warning_msg
    )


@router.post("/extract-text", response_model=ExtractResponse, status_code=status.HTTP_200_OK)
def extract_text(
    request: ExtractTextRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Normalizes and cleans pasted plain text medical report.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty or contain only whitespace."
        )

    raw_text = extract_text_from_plain_text(request.text)
    noise_stripped = strip_document_noise(raw_text)
    cleaned_text = clean_extracted_text(noise_stripped)

    word_count = len(cleaned_text.split())
    char_count = len(cleaned_text)

    return ExtractResponse(
        success=True,
        extracted_text=cleaned_text,
        character_count=char_count,
        word_count=word_count,
        source_type="text",
        warning=None
    )
