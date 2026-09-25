import re
import nltk

# Ensure NLTK data resources are downloaded on first run
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords

# Dictionary of standard medical abbreviations and their expanded forms
MEDICAL_ABBREVIATIONS = {
    "pt": "patient",
    "hx": "history",
    "dx": "diagnosis",
    "tx": "treatment",
    "rx": "prescription",
    "f/u": "follow-up",
    "b.i.d.": "twice a day",
    "bid": "twice a day",
    "t.i.d.": "three times a day",
    "tid": "three times a day",
    "q.i.d.": "four times a day",
    "qid": "four times a day",
    "p.o.": "by mouth",
    "po": "by mouth",
    "p.r.n.": "as needed",
    "prn": "as needed",
    "s/p": "status post",
    "w/o": "without",
    "c/o": "complaining of",
    "sob": "shortness of breath",
    "bpm": "beats per minute",
    "bp": "blood pressure",
    "hr": "heart rate",
    "rr": "respiratory rate",
    "ecg": "electrocardiogram",
    "ekg": "electrocardiogram",
    "lvef": "left ventricular ejection fraction",
}


def segment_sentences(text: str) -> list[str]:
    """
    Segments raw medical report text into clean individual sentences.
    Respects document structure by handling section headers, bullet points, and newlines.

    Args:
        text (str): Input text string.

    Returns:
        list[str]: List of segmented sentences.
    """
    if not text or not text.strip():
        return []

    # Strip divider line banners (e.g. === or ---)
    cleaned = re.sub(r'^[=_\-]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Split by line breaks first to preserve structural report lines
    raw_lines = [line.strip() for line in cleaned.splitlines() if line.strip()]

    sentences = []
    for line in raw_lines:
        # Remove bullet symbols or line numbers (e.g., "- ", "1. ", "• ")
        clean_line = re.sub(r'^[•\-\*\d+\.]\s*', '', line).strip()
        if not clean_line:
            continue

        # Use NLTK sentence tokenizer for sub-sentence boundaries
        sub_sents = sent_tokenize(clean_line)
        for s in sub_sents:
            s_clean = s.strip()
            if s_clean and len(s_clean) > 3:
                sentences.append(s_clean)

    return sentences


def normalize_medical_text(text: str) -> str:
    """
    Normalizes medical text by expanding common medical abbreviations.
    Uses case-insensitive, word-boundary aware regex replacement to avoid changing substrings.

    Args:
        text (str): Input medical report text.

    Returns:
        str: Text with expanded medical abbreviations.
    """
    if not text:
        return ""

    normalized = text
    for abbr, expansion in MEDICAL_ABBREVIATIONS.items():
        pattern = r'(?<!\w)' + re.escape(abbr) + r'(?!\w)'
        normalized = re.sub(pattern, expansion, normalized, flags=re.IGNORECASE)

    return normalized


def remove_stopwords_for_analysis(tokens: list[str]) -> list[str]:
    """
    Removes standard English stopwords from a token list.

    NOTE: This function is strictly intended for internal NLP analysis, scoring,
    and keyword/TextRank sentence ranking in later stages.
    It is NEVER applied to the actual text or summary rendered to the user,
    ensuring clinical reports remain fully readable and grammatically complete.

    Args:
        tokens (list[str]): List of string tokens.

    Returns:
        list[str]: Filtered list of tokens with stopwords removed.
    """
    stop_words = set(stopwords.words('english'))
    return [token for token in tokens if token.lower() not in stop_words and token.isalnum()]
