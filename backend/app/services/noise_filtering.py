import re
from collections import Counter


def strip_document_noise(text: str) -> str:
    """
    Strips common non-clinical boilerplate, noise, letterheads, footers, phone numbers,
    emails, address lines, QR code garbled artifacts, and signature blocks from document text.

    Conservatively retains all clinical findings, medical entities, lab values, unit names,
    reference ranges, patient info, and physician notes.

    Args:
        text (str): Extracted raw text or OCR output.

    Returns:
        str: Cleaned text with non-clinical noise removed.
    """
    if not text:
        return ""

    lines = text.splitlines()

    # Pre-pass: Detect repeated lines across document (e.g. repeated page headers/footers)
    line_counts = Counter([l.strip() for l in lines if l.strip()])
    repeated_lines = {line for line, count in line_counts.items() if count > 1 and len(line) > 10}

    filtered_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 1. Skip exact repeated header/footer lines that appear multiple times
        if stripped in repeated_lines:
            # Preserve if it contains obvious clinical keywords or test results
            if not _contains_clinical_data(stripped):
                continue

        # 2. Skip Page numbers (e.g. "Page 1 of 2", "Page 2/3", "Page: 1")
        if re.match(r'^(page\s*\d+(\s*(of|/)\s*\d+)?|\d+\s*(of|/)\s*\d+)$', stripped, re.IGNORECASE):
            continue

        # 3. Skip UI navigation / web link text
        if re.search(r'\b(view details|view report|click here|download pdf|print report)\b', stripped, re.IGNORECASE):
            continue

        # 4. Skip standalone URLs / web domains
        if re.match(r'^(https?://|www\.)[^\s]+$', stripped, re.IGNORECASE) or re.search(r'\bwww\.[a-z0-9-]+\.[a-z]{2,}\b', stripped, re.IGNORECASE):
            # If line is ONLY URL or contact site
            if len(stripped.split()) <= 3:
                continue

        # 5. Skip email addresses when line is primarily email/contact info
        if re.search(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', stripped):
            if not _contains_clinical_data(stripped):
                continue

        # 6. Skip phone / fax / mobile contact numbers
        if re.search(r'\b(tel|phone|ph|mobile|mob|fax|call)\s*[:.-]?\s*\+?\d', stripped, re.IGNORECASE):
            if not _contains_clinical_data(stripped):
                continue
        if re.match(r'^(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}$', stripped):
            continue

        # 6b. Skip registration / license numbers (e.g. "Reg. No. 2005/09/3695", "Reg. No. 2011/04/5521")
        if re.search(r'\b(reg\.?\s*no\.?|registration|lic\.?\s*no\.?|license|gstin|gst|accession)\b', stripped, re.IGNORECASE):
            if not _contains_clinical_data(stripped):
                continue

        # 7. Skip Address & Location header blocks
        if re.search(r'\b(pin|zip|pincode)\s*[:.-]?\s*\d{5,6}\b', stripped, re.IGNORECASE):
            if not _contains_clinical_data(stripped):
                continue
        if re.search(r'\b(location|address|c/o|opposite|near|road|street|marg|chs|plot no|opp\.|flr|floor|building|nagar|colony)\b', stripped, re.IGNORECASE):
            if not _contains_clinical_data(stripped) and len(stripped) < 90:
                continue

        # 8. Skip Lab / Clinic Letterhead headers
        if re.search(r'\b(diagnostic|diagnostics|pathology|pathlab|laboratory|labs|health care|healthcare|hospital|clinic|medical centre|center)\b', stripped, re.IGNORECASE):
            if not _contains_clinical_data(stripped) and len(stripped) < 70:
                continue

        # 9. Skip signature lines / designations when standalone
        if re.search(r'\b(consultant pathologist|pathologist|chief officer|lab incharge|md pathology|d\.p\.b|dnb|signature)\b', stripped, re.IGNORECASE):
            if not _contains_clinical_data(stripped):
                continue

        # 10. Skip QR code / Barcode misreads (short garbled non-word strings)
        if _is_garbled_qr_artifact(stripped):
            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines)


def _contains_clinical_data(line: str) -> bool:
    """
    Helper function to check if a line contains essential clinical data
    (test names, numbers with units, reference ranges, patient demographics, diagnoses).
    """
    # Check for clinical units or lab measurement patterns (e.g. mg/dL, g/dL, %, /uL, mmol/L, x10^3)
    if re.search(r'\b(mg/dl|g/dl|mmol/l|u/l|iu/l|/ul|%|pg|ng/ml|mEq/L|mmHg|bpm)\b', line, re.IGNORECASE):
        return True

    # Check for reference range pattern (e.g. 13.5 - 17.5, < 200, 4.0-10.0)
    if re.search(r'\d+(\.\d+)?\s*[-–—]\s*\d+(\.\d+)?', line):
        return True

    # Check for clinical section headers or labels
    clinical_keywords = [
        "patient", "age", "gender", "dob", "mrn", "history", "complaint",
        "impression", "diagnosis", "medication", "treatment", "hemoglobin",
        "wbc", "rbc", "platelet", "glucose", "cholesterol", "triglycerides",
        "creatinine", "urea", "bilirubin", "sgot", "sgpt", "thyroid", "tsh"
    ]
    line_lower = line.lower()
    if any(kw in line_lower for kw in clinical_keywords):
        return True

    return False


def _is_garbled_qr_artifact(line: str) -> bool:
    """
    Detects short OCR misreads of QR codes or barcodes (garbled alphanumeric strings).
    """
    stripped = line.strip()
    if len(stripped) < 4 or len(stripped) > 25:
        return False

    # Check ratio of special non-alphanumeric characters
    special_char_count = len(re.findall(r'[^a-zA-Z0-9\s]', stripped))
    if special_char_count >= 3 and len(stripped.split()) == 1:
        return True

    # Check garbled random mixed-case alphanumeric string without spaces
    if re.match(r'^[a-zA-Z0-9#$@!%&*]{5,20}$', stripped) and not stripped.isalpha():
        # Has numbers + lowercase + uppercase mixed randomly
        has_lower = any(c.islower() for c in stripped)
        has_upper = any(c.isupper() for c in stripped)
        has_digit = any(c.isdigit() for c in stripped)
        if has_lower and has_upper and has_digit and len(stripped.split()) == 1:
            return True

    return False
