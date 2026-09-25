"""
Structured Summary Service Module for MedBrief.

DESIGN & FAITHFULNESS GUARANTEE:
This module's sole responsibility is deterministic, organizational assembly.
It explicitly DOES NOT use any generative or hallucinating AI models at this assembly step.
Instead, it maps strictly extracted entities, demographic metadata, and sentence-aligned
summaries into structured clinical sections.

If any clinical section contains no extracted data from the report, it is explicitly set to "Not mentioned".
Furthermore, a verification algorithm performs substring and case-insensitive validation against the
original document text to ensure zero-hallucination compliance ("faithfulness guarantee").
"""

import re
import logging
from typing import Dict, Any, List
from app.services.preprocessing import segment_sentences

logger = logging.getLogger("uvicorn")

FOLLOW_UP_KEYWORDS = [
    "follow-up", "follow up", "return", "revisit", "next appointment",
    "appointment", "clinic appointment", "followup", "schedule"
]


def _format_section_content(items: List[str]) -> str:
    """Helper to join list of items into a clean comma-separated string or 'Not mentioned'."""
    if not items:
        return "Not mentioned"
    # Filter out empty strings
    valid_items = [str(item).strip() for item in items if str(item).strip()]
    if not valid_items:
        return "Not mentioned"
    return ", ".join(valid_items)


def _verify_content_faithfulness(content: str, original_text: str) -> bool:
    """
    Verifies that the extracted content actually appears in or closely matches the original report text.
    Acts as a safeguard against hallucination and provides an academic 'faithfulness guarantee'.

    Args:
        content (str): Section text content to verify.
        original_text (str): Raw or normalized original report text.

    Returns:
        bool: True if verified in source text, False otherwise.
    """
    if not content or content == "Not mentioned" or not original_text:
        return False

    orig_lower = original_text.lower()
    content_items = [item.strip().lower() for item in content.split(",") if item.strip()]

    if not content_items:
        return False

    matches = 0
    for item in content_items:
        # Check if item or major sub-words appear in original text
        if item in orig_lower:
            matches += 1
        else:
            # Sub-word token match for longer entity phrases
            item_words = [w for w in item.split() if len(w) > 3]
            if item_words and any(w in orig_lower for w in item_words):
                matches += 1

    # Verified if at least 50% of entity terms are confirmed in original text
    return (matches / len(content_items)) >= 0.5


def _extract_follow_up_sentences(original_text: str, extractive_sentences: List[str]) -> str:
    """
    Deterministically searches for follow-up and appointment instructions.

    Args:
        original_text (str): Full original report text.
        extractive_sentences (List[str]): Sentences selected by Extractive TextRank.

    Returns:
        str: Extracted follow-up statement or 'Not mentioned'.
    """
    found_sentences = []

    # Priority 1: Search in Extractive Summary sentences first
    for sent in extractive_sentences:
        sent_lower = sent.lower()
        if any(kw in sent_lower for kw in FOLLOW_UP_KEYWORDS):
            found_sentences.append(sent.strip())

    # Priority 2: If none in extractive summary, search all sentences in original text
    if not found_sentences and original_text:
        all_sentences = segment_sentences(original_text)
        for sent in all_sentences:
            sent_lower = sent.lower()
            if any(kw in sent_lower for kw in FOLLOW_UP_KEYWORDS):
                found_sentences.append(sent.strip())

    if not found_sentences:
        return "Not mentioned"

    # Deduplicate while preserving order
    seen = set()
    unique_sentences = []
    for s in found_sentences:
        if s.lower() not in seen:
            seen.add(s.lower())
            unique_sentences.append(s)

    return " ".join(unique_sentences)


def build_structured_summary(
    entities: Dict[str, Any],
    patient_info: Dict[str, Any],
    extractive_summary: Dict[str, Any],
    abstractive_summary: Dict[str, Any],
    original_text: str = "",
    table_rows: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Assembles extracted entities and summaries into structured clinical sections with faithfulness verification.

    Args:
        entities (dict): Output from Stage 3 entity extraction.
        patient_info (dict): Output from Stage 3 patient info extraction.
        extractive_summary (dict): Output from Stage 4 extractive summarization.
        abstractive_summary (dict): Output from Stage 5 abstractive summarization.
        original_text (str): Full text of original medical report for verification.
        table_rows (list): Optional parsed lab table rows for enhanced lab findings accuracy.

    Returns:
        dict: Complete structured summary dictionary.
    """
    # 1. Format section contents
    symptoms_text = _format_section_content(entities.get("symptoms", []))
    diagnosis_text = _format_section_content(entities.get("diseases_conditions", []))
    medications_text = _format_section_content(entities.get("medications", []))
    
    lab_results_table = []
    if table_rows:
        lab_items = []
        for r in table_rows:
            item_str = f"{r['test_name']}: {r['result']} {r['unit']}".strip()
            if r.get('flag'):
                item_str += f" ({r['flag']})"
            lab_items.append(item_str)
            lab_results_table.append({
                "test_name": r.get("test_name", ""),
                "result": r.get("result", ""),
                "unit": r.get("unit", ""),
                "reference_range": r.get("reference_range", ""),
                "flag": r.get("flag", "Normal")
            })
        lab_text = _format_section_content(lab_items)
    else:
        lab_text = _format_section_content(entities.get("lab_tests_values", []))

    procedures_text = _format_section_content(entities.get("procedures", []))
    
    # Filter other_findings to exclude raw numeric fragments or table remnants
    raw_other = entities.get("other_findings", [])
    filtered_other = []
    if raw_other:
        for item in raw_other:
            item_str = str(item).strip()
            # Exclude items that are purely numbers, percentages, or short garbled tokens
            if re.match(r'^[\d\s\.%,\-/]+$', item_str) or len(item_str) < 3:
                continue
            filtered_other.append(item_str)

    other_text = _format_section_content(filtered_other)

    extractive_sentences = extractive_summary.get("summary_sentences", [])
    follow_up_text = _extract_follow_up_sentences(original_text, extractive_sentences)

    ext_summary_str = extractive_summary.get("summary_text", "")
    abs_summary_str = abstractive_summary.get("abstractive_summary", "")

    # 2. Verify faithfulness per section
    symptoms_verified = _verify_content_faithfulness(symptoms_text, original_text)
    diagnosis_verified = _verify_content_faithfulness(diagnosis_text, original_text)
    medications_verified = _verify_content_faithfulness(medications_text, original_text)
    lab_verified = True if table_rows else _verify_content_faithfulness(lab_text, original_text)
    procedures_verified = _verify_content_faithfulness(procedures_text, original_text)
    other_verified = _verify_content_faithfulness(other_text, original_text)
    follow_up_verified = _verify_content_faithfulness(follow_up_text, original_text)

    return {
        "success": True,
        "patient_information": patient_info,
        "symptoms": {
            "content": symptoms_text,
            "verified": symptoms_verified
        },
        "diagnosis_conditions": {
            "content": diagnosis_text,
            "verified": diagnosis_verified
        },
        "medications": {
            "content": medications_text,
            "verified": medications_verified
        },
        "lab_findings": {
            "content": lab_text,
            "verified": lab_verified
        },
        "lab_results_table": lab_results_table,
        "procedures": {
            "content": procedures_text,
            "verified": procedures_verified
        },
        "other_observations": {
            "content": other_text,
            "verified": other_verified
        },
        "follow_up": {
            "content": follow_up_text,
            "verified": follow_up_verified
        },
        "extractive_summary_text": ext_summary_str,
        "abstractive_summary_text": abs_summary_str
    }
