"""
Table to Narrative Preprocessing Service for MedBrief.

Converts structured tabular lab report data (e.g. test name, numeric result, flag, reference range, unit)
into fluently phrased clinical narrative sentences before passing text to abstractive & extractive summarizers.
Also strips disclaimer / synthetic boilerplate lines so summarization models do not latch onto non-medical footers.
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("uvicorn")

# Expanded pattern for common medical & lab units (including OCR variants)
UNITS = r'(?:gm%|g%|gm/dl|gm/dL|g/dL|mg/dL|U/L|IU/L|uIU/mL|µIU/mL|mil/uL|thou/uL|10\^3/uL|10\^6/uL|mcg/dL|ng/dL|ng/mL|pg/mL|%|mmol/L|mEq/L|g/L|fl|fL|pg|/cmm|mil/cmm|mil\./cmm|mil\./emm|/emm|emm|cmm|ratio)'

# Pattern for qualitative lab results
QUALITATIVE_RESULTS = {"positive", "negative", "trace", "reactive", "non-reactive", "nil", "normal", "abnormal", "absent", "present"}

# Pattern for flags
FLAGS = r'(?:High|Low|Elevated|Decreased|Abnormal|Normal|H|L)'

# List of noise lines / boilerplate substrings to remove from text before summarization
BOILERPLATE_SUBSTRINGS = [
    "synthetic medical report",
    "test data only",
    "not a real patient",
    "does not represent a real patient",
    "for testing purposes only",
    "confidential laboratory report",
    "electronically signed by",
    "end of report",
    "page 1 of 1",
    "page 1 of 2",
    "lab director:",
]

# Blacklist of administrative, demographic, contact, and non-clinical label patterns
ADMIN_LABEL_BLACKLIST = [
    "reg. no.", "reg no", "registration", "reg.no", "reg.no.", "mobile", "phone",
    "contact", "tel", "fax", "ph.", "c/o", "address", "location", "pin", "pincode",
    "gst", "license", "lic. no.", "lic no", "accession", "patient id", "ref id",
    "patient name", "patient", "name", "ref by", "doctor", "dr.", "dr", "invoice",
    "receipt", "sample date", "report date", "pathologist", "mbbs", "sex", "gender",
    "age", "dob", "mrn"
]

# Regex for divider lines like ===== or -----
DIVIDER_PATTERN = re.compile(r'^[=\-_*]{3,}$')

# Robust table row regex to match flattened tabular lab lines (handles optional colons, spacing, units, flags)
TABLE_ROW_PATTERN = re.compile(
    r'^\s*[\-\*•]?\s*'  # Optional bullet or OCR bullet misread
    r'(?P<test_name>[A-Za-z0-9\s\(\)/_\-\.,]+?)\s*'  # Test name
    r'[:;=I]*\s*'  # Optional colon/semicolon/equals/OCR separator
    r'(?P<result>[<>]?\s*\d+(?:\.\d+)?|[A-Za-z]+)\s*'  # Result value (numeric or qualitative string)
    r'(?P<unit1>' + UNITS + r')?\s*'  # Optional unit after result
    r'(?P<flag>' + FLAGS + r')?\s*'  # Optional flag (High/Low/Elevated etc)
    r'(?:(?:ref(?:erence)?\s*(?:range|interval)?:?|normal:?)\s*)?'  # Optional "Ref Range:" label
    r'(?P<ref_range>(?:[<>]?\s*\d+(?:\.\d+)?\s*(?:-|to|—|–)\s*\d+(?:\.\d+)?|[<>]?\s*\d+(?:\.\d+)?))?\s*'  # Reference range
    r'(?P<unit2>' + UNITS + r')?\s*$',  # Optional unit after reference range
    re.IGNORECASE
)


def strip_boilerplate_and_disclaimers(text: str) -> str:
    """
    Strips synthetic data warnings, divider lines, and footer boilerplate from clinical text.

    Args:
        text (str): Raw input text.

    Returns:
        str: Cleaned text free of disclaimers and boilerplate footers.
    """
    if not text:
        return ""

    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if DIVIDER_PATTERN.match(stripped):
            continue

        line_lower = stripped.lower()
        if any(bp in line_lower for bp in BOILERPLATE_SUBSTRINGS):
            continue

        cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines)


def _sanitize_ocr_result_digit(test_name: str, result_str: str, ref_range_str: str) -> str:
    """
    Sanity checks numeric OCR results against reference range to detect common OCR digit-swap errors.
    e.g. OCR misreading ': 34.2' or '15.1' as '234.2' or '215.1' (leading colon misread as digit '2' or '7').
    """
    if not result_str or not ref_range_str:
        return result_str

    try:
        val = float(result_str)
        m = re.search(r'(\d+(?:\.\d+)?)\s*[-–—to]+\s*(\d+(?:\.\d+)?)', ref_range_str)
        if m:
            low_ref = float(m.group(1))
            high_ref = float(m.group(2))
            
            # If value is > 3x the upper reference limit and starts with '2' or '7'
            if val > high_ref * 3.0 and len(result_str) >= 3:
                stripped_val_str = result_str[1:]
                try:
                    stripped_val = float(stripped_val_str)
                    # Check if stripped value falls near or inside reasonable reference boundaries
                    if (low_ref * 0.5) <= stripped_val <= (high_ref * 2.5):
                        logger.warning(
                            f"[OCR DIGIT SANITY] Corrected misread OCR result '{result_str}' to '{stripped_val_str}' "
                            f"for test '{test_name}' (ref range: {ref_range_str})"
                        )
                        return stripped_val_str
                except ValueError:
                    pass
    except ValueError:
        pass

    return result_str


def _determine_flag(result_str: str, ref_range_str: str, existing_flag: str) -> str:
    """
    Calculates 'High'/'Low'/'Normal' flag if reference range is present or explicit flag is in source text.
    If no reference range exists and no explicit flag was in source, returns empty string ("").
    """
    if existing_flag:
        flag_upper = existing_flag.upper()
        if flag_upper in ["H", "HIGH", "ELEVATED"]:
            return "High"
        elif flag_upper in ["L", "LOW", "DECREASED"]:
            return "Low"
        elif flag_upper in ["NORMAL"]:
            return "Normal"

    if not result_str or not ref_range_str:
        return ""  # Do NOT default to "Normal" if unflagged in source text

    try:
        val = float(result_str)
        m = re.search(r'(\d+(?:\.\d+)?)\s*[-–—to]+\s*(\d+(?:\.\d+)?)', ref_range_str)
        if m:
            low_ref = float(m.group(1))
            high_ref = float(m.group(2))
            if val < low_ref:
                return "Low"
            elif val > high_ref:
                return "High"
            else:
                return "Normal"

        # Check for "< 200" or "> 40" reference range formats
        m_less = re.search(r'<\s*(\d+(?:\.\d+)?)', ref_range_str)
        if m_less:
            max_val = float(m_less.group(1))
            return "High" if val > max_val else "Normal"

        m_greater = re.search(r'>\s*(\d+(?:\.\d+)?)', ref_range_str)
        if m_greater:
            min_val = float(m_greater.group(1))
            return "Low" if val < min_val else "Normal"

    except ValueError:
        pass

    return ""


def detect_tabular_lab_data(text: str) -> List[Dict[str, str]]:
    """
    Detects tabular lab report lines from document text.

    Args:
        text (str): Input document text.

    Returns:
        List[Dict[str, str]]: List of parsed lab result dicts with keys:
            test_name, result, flag, reference_range, unit.
    """
    if not text:
        return []

    table_rows = []
    header_keywords = {
        "test name", "tests", "result", "results", "flag", "reference range",
        "units", "unit", "ref range", "biological reference", "reference", "range"
    }

    lines = text.splitlines()

    for line_idx, line in enumerate(lines):
        line_str = line.strip()
        if not line_str:
            continue

        # Ignore obvious table column header lines
        words_lower = set(re.findall(r'\b[a-z]+\b', line_str.lower()))
        if len(words_lower.intersection(header_keywords)) >= 2:
            continue

        # Clean line for matching
        cleaned_line = re.sub(r'^[^\w\s]+', '', line_str).strip()
        # Replace garbled OCR separator patterns like " I W/ " or " QR PIG) " before numbers
        cleaned_line = re.sub(r'\s+[A-Za-z\(\)\s]*[/\)]\s*(?=\d)', ' : ', cleaned_line)

        # Try matching table row pattern
        match = TABLE_ROW_PATTERN.match(cleaned_line) or TABLE_ROW_PATTERN.match(line_str)
        if match:
            gd = match.groupdict()
            test_name = gd["test_name"].strip()
            test_name_lower = test_name.lower()

            # Rule 1: Administrative Blacklist Check
            if any(black in test_name_lower for black in ADMIN_LABEL_BLACKLIST):
                logger.info(f"[TABLE PARSER REJECT] Line {line_idx+1}: Administrative blacklist match '{test_name}'")
                continue

            # Require test_name to contain letters
            if not re.search(r'[A-Za-z]', test_name):
                continue

            raw_result = gd["result"].strip() if gd["result"] else ""
            raw_flag = gd["flag"].strip() if gd["flag"] else ""
            ref_range = gd["ref_range"].strip() if gd["ref_range"] else ""
            unit = (gd["unit1"] or gd["unit2"] or "").strip()

            # Rule 2: Result Value Validation (must be numeric or known qualitative result)
            is_numeric = bool(re.match(r'^[<>]?\s*\d+(?:\.\d+)?$', raw_result))
            is_qualitative = raw_result.lower() in QUALITATIVE_RESULTS
            if not is_numeric and not is_qualitative:
                logger.info(f"[TABLE PARSER REJECT] Line {line_idx+1}: Non-numeric and non-qualitative result '{raw_result}' for test '{test_name}'")
                continue

            # Rule 3: Mandatory Unit or Reference Range Requirement
            # Reject candidate rows where BOTH unit is empty AND reference_range is empty
            if not unit and not ref_range:
                logger.info(f"[TABLE PARSER REJECT] Line {line_idx+1}: Missing both Unit and Ref Range for '{test_name}' ({raw_result})")
                continue

            # Normalize OCR unit symbols
            if unit.lower() in ["jemm", "miljemm", "/emm", "emm"]:
                unit = "/cmm" if "mil" not in unit.lower() else "mil./cmm"
            elif unit.lower() in ["gnvdi", "gm%"]:
                unit = "gm/dL" if "gnvdi" in unit.lower() else "gm%"

            # Sanity check OCR result digit misreads
            sanitized_result = _sanitize_ocr_result_digit(test_name, raw_result, ref_range)

            # Auto-calculate or normalize flag (leave blank if unflagged and no ref range)
            calculated_flag = _determine_flag(sanitized_result, ref_range, raw_flag)

            row_data = {
                "test_name": test_name,
                "result": sanitized_result,
                "flag": calculated_flag,
                "reference_range": ref_range,
                "unit": unit
            }
            table_rows.append(row_data)
            logger.info(f"[TABLE PARSER MATCH] Line {line_idx+1}: MATCHED '{line_str}' -> {row_data}")

    logger.info(f"[TABLE PARSER SUMMARY] Total Table Rows Detected: {len(table_rows)}")
    return table_rows


def generate_narrative_from_table(table_rows: List[Dict[str, str]]) -> str:
    """
    Converts a list of parsed lab table rows into a fluent narrative paragraph.

    Args:
        table_rows (List[Dict[str, str]]): List of table row dictionaries.

    Returns:
        str: Paragraph containing generated narrative sentences.
    """
    if not table_rows:
        return ""

    sentences = []
    for row in table_rows:
        test_name = row.get("test_name", "").strip()
        result = row.get("result", "").strip()
        flag = row.get("flag", "").strip()
        ref = row.get("reference_range", "").strip()
        unit = row.get("unit", "").strip()

        unit_str = f" {unit}" if unit else ""

        if flag.lower() in ["elevated", "high"]:
            if ref:
                ref_formatted = ref.replace("-", " to ")
                sentence = f"{test_name} was elevated at {result}{unit_str}, above the normal reference range of {ref_formatted}{unit_str}."
            else:
                sentence = f"{test_name} was elevated at {result}{unit_str}."
        elif flag.lower() in ["low", "decreased"]:
            if ref:
                ref_formatted = ref.replace("-", " to ")
                sentence = f"{test_name} was low at {result}{unit_str}, below the normal range of {ref_formatted}{unit_str}."
            else:
                sentence = f"{test_name} was low at {result}{unit_str}."
        else:
            if ref:
                sentence = f"{test_name} was within normal range at {result}{unit_str} (reference: {ref}{unit_str})."
            else:
                sentence = f"{test_name} was measured at {result}{unit_str}."

        sentences.append(sentence)

    return " ".join(sentences)
