import time
import re
import json
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db_models import User, Report
from app.api.auth import get_current_user
from app.models.schemas import (
    ExtractTextRequest,
    MedicalInfoResponse,
    ExtractiveSummaryRequest,
    ExtractiveSummaryResponse,
    AbstractiveSummaryRequest,
    AbstractiveSummaryResponse,
    StructuredSummaryResponse,
    EvaluationRequest,
    EvaluationResponse,
)
from app.services.preprocessing import normalize_medical_text, segment_sentences
from app.services.entity_extraction import extract_patient_info, extract_medical_entities
from app.services.extractive_summary import generate_extractive_summary
from app.services.abstractive_summary import generate_abstractive_summary
from app.services.structured_summary import build_structured_summary
from app.services.evaluation import evaluate_summaries
from app.services.noise_filtering import strip_document_noise
from app.services.table_to_narrative import (
    detect_tabular_lab_data,
    generate_narrative_from_table,
    strip_boilerplate_and_disclaimers
)


logger = logging.getLogger("uvicorn")

router = APIRouter()


def preprocess_text_for_summarization(text: str):
    """
    Preprocesses input text before passing to summarizers:
    1. Strips document noise (phone numbers, addresses, emails, UI text).
    2. Strips disclaimer and boilerplate footer lines.
    3. Detects if input text consists of tabular lab data.
    4. If tabular data is present, generates a fluent clinical narrative.
    
    Returns:
        tuple: (text_for_summarization, detected_table_rows)
    """
    cleaned = strip_document_noise(text)
    cleaned = strip_boilerplate_and_disclaimers(cleaned)
    table_rows = detect_tabular_lab_data(cleaned)
    if table_rows:
        narrative = generate_narrative_from_table(table_rows)
        return narrative, table_rows
    return cleaned, []


@router.post("/extract-entities", response_model=MedicalInfoResponse, status_code=status.HTTP_200_OK)
def extract_entities(request: ExtractTextRequest):
    """
    Processes medical report text to:
    1. Normalize medical abbreviations (e.g. pt -> patient, dx -> diagnosis).
    2. Segment text into sentences using NLTK.
    3. Extract patient demographic info (Name, Age, Gender, Date).
    4. Extract categorized verbatim medical entities (diseases, symptoms, meds, lab values, procedures, dates).
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty or contain only whitespace."
        )

    try:
        # Strip document noise and boilerplate disclaimers first
        cleaned_text = strip_document_noise(request.text)
        cleaned_text = strip_boilerplate_and_disclaimers(cleaned_text)

        # Step 1: Normalize medical abbreviations
        normalized_text = normalize_medical_text(cleaned_text)

        # Step 2: Segment sentences
        sentences = segment_sentences(normalized_text)

        # Step 3: Extract patient info
        patient_info = extract_patient_info(request.text)

        # Step 4: Extract medical entities
        entities = extract_medical_entities(normalized_text)

        return MedicalInfoResponse(
            success=True,
            sentence_count=len(sentences),
            normalized_text=normalized_text,
            patient_info=patient_info,
            entities=entities,
            warning=None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during medical entity extraction: {str(e)}"
        )


@router.post("/summarize-extractive", response_model=ExtractiveSummaryResponse, status_code=status.HTTP_200_OK)
def summarize_extractive(request: ExtractiveSummaryRequest):
    """
    Generates an extractive text summary using TextRank graph algorithm.
    Selects the most central original sentences and returns them in chronological order.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty or contain only whitespace."
        )

    try:
        text_to_summarize, _ = preprocess_text_for_summarization(request.text)
        summary_result = generate_extractive_summary(
            text=text_to_summarize,
            num_sentences=request.num_sentences
        )

        return ExtractiveSummaryResponse(
            success=True,
            summary_sentences=summary_result["summary_sentences"],
            summary_text=summary_result["summary_text"],
            original_sentence_count=summary_result["original_sentence_count"],
            summary_sentence_count=summary_result["summary_sentence_count"],
            compression_ratio=summary_result["compression_ratio"],
            warning=summary_result["warning"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during extractive summarization: {str(e)}"
        )


@router.post("/summarize-abstractive", response_model=AbstractiveSummaryResponse, status_code=status.HTTP_200_OK)
def summarize_abstractive(request: AbstractiveSummaryRequest):
    """
    Generates an abstractive text summary using HuggingFace Transformers (distilbart-cnn-6-6).
    Synthesizes a new paraphrased narrative summary of the medical report.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty or contain only whitespace."
        )

    try:
        text_to_summarize, _ = preprocess_text_for_summarization(request.text)
        start_time = time.time()
        summary_result = generate_abstractive_summary(
            text=text_to_summarize,
            max_length=request.max_length,
            min_length=request.min_length
        )
        elapsed_seconds = round(time.time() - start_time, 2)

        return AbstractiveSummaryResponse(
            success=True,
            abstractive_summary=summary_result["abstractive_summary"],
            chunks_processed=summary_result["chunks_processed"],
            model_used=summary_result["model_used"],
            input_word_count=summary_result["input_word_count"],
            summary_word_count=summary_result["summary_word_count"],
            processing_time_seconds=elapsed_seconds,
            warning=summary_result["warning"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during abstractive summarization: {str(e)}"
        )


@router.post("/analyze-full", response_model=StructuredSummaryResponse, status_code=status.HTTP_200_OK)
def analyze_full(
    request: ExtractTextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Primary end-to-end pipeline endpoint for MedBrief.
    Sequentially executes:
    1. Text Normalization
    2. Medical Entity & Patient Info Extraction
    3. Extractive TextRank Summarization
    4. Abstractive Transformer Summarization
    5. Deterministic Structured Summary Assembly & Faithfulness Verification
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty or contain only whitespace."
        )

    pipeline_start = time.time()

    # Preprocess text (table-to-narrative & disclaimer removal)
    cleaned_source = strip_boilerplate_and_disclaimers(strip_document_noise(request.text))
    text_to_summarize, table_rows = preprocess_text_for_summarization(request.text)

    # Step 1: Text Normalization
    try:
        t0 = time.time()
        normalized_text = normalize_medical_text(cleaned_source)
        t1 = time.time()
        logger.info(f"[PIPELINE TIMING] Step 1 (Normalization): {round(t1 - t0, 4)}s")
    except Exception as e:
        logger.error(f"[PIPELINE ERROR] Step 1 (Normalization) failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline processing failed at Stage 1 (Text Normalization): {str(e)}"
        )

    # Step 2: Entity & Patient Info Extraction
    try:
        t0 = time.time()
        patient_info = extract_patient_info(request.text)
        entities = extract_medical_entities(normalized_text)
        t1 = time.time()
        logger.info(f"[PIPELINE TIMING] Step 2 (Entity & Patient Extraction): {round(t1 - t0, 4)}s")
    except Exception as e:
        logger.error(f"[PIPELINE ERROR] Step 2 (Entity Extraction) failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline processing failed at Stage 2 (Medical Entity Extraction): {str(e)}"
        )

    # Step 3: Extractive TextRank Summarization
    try:
        t0 = time.time()
        extractive_res = generate_extractive_summary(text_to_summarize, num_sentences=5)
        t1 = time.time()
        logger.info(f"[PIPELINE TIMING] Step 3 (Extractive Summarization): {round(t1 - t0, 4)}s")
    except Exception as e:
        logger.error(f"[PIPELINE ERROR] Step 3 (Extractive Summarization) failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline processing failed at Stage 3 (Extractive Summarization): {str(e)}"
        )

    # Step 4: Abstractive Transformer Summarization
    try:
        t0 = time.time()
        abstractive_res = generate_abstractive_summary(text_to_summarize, max_length=150, min_length=40)
        t1 = time.time()
        logger.info(f"[PIPELINE TIMING] Step 4 (Abstractive Summarization): {round(t1 - t0, 4)}s")
    except Exception as e:
        logger.error(f"[PIPELINE ERROR] Step 4 (Abstractive Summarization) failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline processing failed at Stage 4 (Abstractive Summarization): {str(e)}"
        )

    # Step 5: Structured Summary Assembly & Faithfulness Verification
    try:
        t0 = time.time()
        structured_res = build_structured_summary(
            entities=entities,
            patient_info=patient_info,
            extractive_summary=extractive_res,
            abstractive_summary=abstractive_res,
            original_text=request.text,
            table_rows=table_rows
        )
        t1 = time.time()
        logger.info(f"[PIPELINE TIMING] Step 5 (Structured Assembly & Verification): {round(t1 - t0, 4)}s")
    except Exception as e:
        logger.error(f"[PIPELINE ERROR] Step 5 (Structured Assembly) failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline processing failed at Stage 5 (Structured Summary Assembly): {str(e)}"
        )

    # Step 6: Save Report History linked to logged-in user
    try:
        w_count = len(request.text.split())
        s_count = len([s for s in re.split(r'[.!?]+', request.text) if s.strip()])
        p_name = patient_info.get("patient_name") if patient_info else None
        
        report_entry = Report(
            user_id=current_user.id,
            patient_name=p_name if p_name != "Not mentioned" else None,
            source_type="text",
            word_count=w_count,
            sentence_count=s_count,
            structured_summary_json=json.dumps(structured_res),
            extractive_summary=extractive_res.get("summary_text") if extractive_res else None,
            abstractive_summary=abstractive_res.get("abstractive_summary") if abstractive_res else None
        )
        db.add(report_entry)
        db.commit()
    except Exception as save_err:
        logger.warning(f"[DATABASE WARNING] Failed to persist report record: {save_err}")

    pipeline_total = round(time.time() - pipeline_start, 4)
    logger.info(f"[PIPELINE TIMING] TOTAL FULL PIPELINE DURATION: {pipeline_total}s")

    return StructuredSummaryResponse(**structured_res)


@router.post("/evaluate", response_model=EvaluationResponse, status_code=status.HTTP_200_OK)
def evaluate_summary_quality(request: EvaluationRequest):
    """
    Standalone academic evaluation endpoint for MedBrief.
    Computes ROUGE-1, ROUGE-2, and ROUGE-L precision, recall, and F1 scores comparing
    extractive and abstractive summaries against a user-provided reference (gold-standard) summary.
    """
    if not request.extractive_summary or not request.extractive_summary.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extractive summary cannot be empty or contain only whitespace."
        )
    if not request.abstractive_summary or not request.abstractive_summary.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Abstractive summary cannot be empty or contain only whitespace."
        )
    if not request.reference_summary or not request.reference_summary.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reference summary cannot be empty or contain only whitespace."
        )

    try:
        evaluation_res = evaluate_summaries(
            extractive_summary=request.extractive_summary,
            abstractive_summary=request.abstractive_summary,
            reference_summary=request.reference_summary
        )

        return EvaluationResponse(
            success=True,
            extractive_scores=evaluation_res["extractive_scores"],
            abstractive_scores=evaluation_res["abstractive_scores"],
            comparison_note=evaluation_res["comparison_note"]
        )
    except Exception as e:
        logger.error(f"[EVALUATION ERROR] ROUGE computation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during ROUGE evaluation: {str(e)}"
        )


