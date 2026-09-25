import re
import spacy

# Load spaCy NLP model once at module initialization for optimal performance
try:
    nlp = spacy.load("en_core_sci_sm")
    MODEL_NAME = "en_core_sci_sm"
except Exception:
    try:
        nlp = spacy.load("en_core_web_sm")
        MODEL_NAME = "en_core_web_sm"
    except Exception as e:
        raise RuntimeError(f"Could not load spaCy model: {str(e)}") from e

from app.services.table_to_narrative import detect_tabular_lab_data

# Pre-compiled regex patterns for patient information extraction
PATIENT_NAME_PATTERN = re.compile(
    r'(?:Patient Name|Patient|Pt Name)\s*[:=]\s*([A-Za-z0-9\s\(\)\.]+?)(?=\s*(?:\||Age|Gender|DOB|MRN|\n|$))',
    re.IGNORECASE
)
AGE_PATTERN = re.compile(
    r'(?:Age)\s*[:=]\s*(\d{1,3})|(\d{1,3})\s*[- ]*(?:year|yr)[- ]*old',
    re.IGNORECASE
)
GENDER_PATTERN = re.compile(
    r'(?:Gender|Sex)\s*[:=]\s*(Male|Female|Other|M|F)\b|\b(Male|Female)\b',
    re.IGNORECASE
)
REPORT_DATE_PATTERN = re.compile(
    r'(?:Date of Visit|Date|Visit Date|DOS)\s*[:=]\s*(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|[A-Z][a-z]+\s+\d{1,2},\s*\d{4})',
    re.IGNORECASE
)

# Curated medical rule-based lists & patterns for hybrid extraction
COMMON_MEDICATIONS_PATTERN = re.compile(
    r'\b(?:[A-Za-z]+(?:statin|pril|olol|sartan|pine|cin|mab|ide|fen|zole|pam|lam|cillin|mycin)|Lisinopril|Atorvastatin|Aspirin|Metformin|Levothyroxine|Amlodipine|Metoprolol|Omeprazole|Albuterol|Gabapentin|Furosemide)'
    r'(?:\s+\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|units?))?\b',
    re.IGNORECASE
)


LAB_TESTS_VALS_PATTERN = re.compile(
    r'\b(BP|Blood Pressure|HR|Heart Rate|RR|SpO2|Troponin[^\n,:]*|BNP|Lipid Panel|Total Cholesterol|LDL|HDL|Triglycerides|LVEF|Left Ventricular Ejection Fraction|HbA1c|WBC|RBC|Platelets|Glucose|Creatinine|BUN)'
    r'\s*[:=]?\s*([<>]?\s*\d+(?:\.\d+)?\s*(?:mg/dL|g/dL|pg/mL|ng/mL|mmHg|bpm|%|/min|°F|°C)?)\b',
    re.IGNORECASE
)

COMMON_SYMPTOMS = [
    "shortness of breath", "chest tightness", "chest pain", "dyspnea", "exertional dyspnea",
    "fever", "cough", "fatigue", "nausea", "vomiting", "dizziness", "headache",
    "edema", "peripheral edema", "palpitations", "diaphoresis", "syncope", "wheezing", "rales", "rhonchi"
]

COMMON_DISEASES = [
    "hypertension", "essential hypertension", "hyperlipidemia", "acute coronary syndrome",
    "bronchitis", "acute bronchitis", "diabetes", "diabetes mellitus", "hypertensive heart disease",
    "left ventricular hypertrophy", "hypertrophy", "arrhythmia", "pneumonia", "asthma"
]

COMMON_PROCEDURES = [
    "echocardiogram", "electrocardiogram", "ecg", "ekg", "treadmill stress test",
    "stress test", "x-ray", "chest x-ray", "ct scan", "mri", "ultrasound", "biopsy", "auscultation"
]

# Section header noise strings to exclude from generic findings
SECTION_HEADER_NOISE = {
    "patient information", "chief complaint", "clinical history", "physical examination",
    "diagnostic workup", "lab results", "impression", "diagnosis", "treatment plan",
    "recommendations", "synthetic medical report", "test data only", "patient name", "date of visit"
}


def extract_patient_info(text: str) -> dict:
    """
    Extracts basic demographic and visit metadata from the text using regex pattern matching.

    Args:
        text (str): Input report text.

    Returns:
        dict: Patient demographic dictionary with keys: patient_name, age, gender, report_date.
    """
    if not text:
        return {
            "patient_name": "Not mentioned",
            "age": "Not mentioned",
            "gender": "Not mentioned",
            "report_date": "Not mentioned"
        }

    # Patient Name
    name_match = PATIENT_NAME_PATTERN.search(text)
    patient_name = name_match.group(1).strip() if name_match else "Not mentioned"

    # Age
    age_match = AGE_PATTERN.search(text)
    if age_match:
        age = age_match.group(1) or age_match.group(2)
    else:
        age = "Not mentioned"

    # Gender
    gender_match = GENDER_PATTERN.search(text)
    if gender_match:
        g = (gender_match.group(1) or gender_match.group(2)).strip()
        if g.upper() in ['M', 'MALE']:
            gender = "Male"
        elif g.upper() in ['F', 'FEMALE']:
            gender = "Female"
        else:
            gender = g.capitalize()
    else:
        gender = "Not mentioned"

    # Report Date
    date_match = REPORT_DATE_PATTERN.search(text)
    report_date = date_match.group(1).strip() if date_match else "Not mentioned"

    return {
        "patient_name": patient_name,
        "age": age,
        "gender": gender,
        "report_date": report_date
    }


def extract_medical_entities(text: str) -> dict:
    """
    Extracts medical entities from the input text using a hybrid approach:
    1. spaCy NLP Named Entity Recognition (NER)
    2. Curated rule-based pattern matching (regex + keyword lists)

    IMPORTANT CLINICAL & LEGAL NOTE:
    This function is strictly NOT diagnosing or interpreting medical data.
    It is ONLY extracting spans of text that already exist verbatim in the report.
    It does not paraphrase or infer entities that are not textually present.

    Args:
        text (str): Cleaned report text.

    Returns:
        dict: Dictionary containing lists of extracted entities categorized by type.
    """
    entities = {
        "diseases_conditions": set(),
        "symptoms": set(),
        "medications": set(),
        "lab_tests_values": set(),
        "procedures": set(),
        "dates": set(),
        "other_findings": set()
    }

    if not text:
        return {k: [] for k in entities}

    # Step 1: spaCy NER Extraction
    doc = nlp(text)
    for ent in doc.ents:
        label = ent.label_.upper()
        ent_text = ent.text.strip()
        if not ent_text or ent_text.lower() in SECTION_HEADER_NOISE:
            continue

        if label in ["DISEASE", "CONDITION", "DISEASE_OR_SYNDROME"]:
            entities["diseases_conditions"].add(ent_text)
        elif label in ["SYMPTOM", "SIGN_OR_SYMPTOM"]:
            entities["symptoms"].add(ent_text)
        elif label in ["CHEMICAL", "DRUG", "MEDICATION"]:
            entities["medications"].add(ent_text)
        elif label in ["DATE", "TIME"]:
            entities["dates"].add(ent_text)
        elif label in ["PROCEDURE"]:
            entities["procedures"].add(ent_text)
        else:
            # Other general entities (filter out structural noise and numbers)
            if len(ent_text) > 3 and not ent_text.isnumeric() and not any(h in ent_text.lower() for h in SECTION_HEADER_NOISE):
                entities["other_findings"].add(ent_text)

    # Step 2: Hybrid Pattern & Keyword Matching (Supplementing Model Output)
    text_lower = text.lower()

    # Rule matching for Medications
    for med_match in COMMON_MEDICATIONS_PATTERN.finditer(text):
        med_str = med_match.group(0).strip()
        if len(med_str) > 2:
            entities["medications"].add(med_str)

    # Rule matching for Lab Tests & Values
    for lab_match in LAB_TESTS_VALS_PATTERN.finditer(text):
        lab_str = lab_match.group(0).strip()
        if len(lab_str) > 2:
            entities["lab_tests_values"].add(lab_str)

    # Detect tabular lab rows and add formatted entries to lab_tests_values
    tab_rows = detect_tabular_lab_data(text)
    for row in tab_rows:
        item = f"{row['test_name']} {row['result']} {row['unit']}".strip()
        if row.get('flag'):
            item += f" ({row['flag']})"
        entities["lab_tests_values"].add(item)

    # Rule matching for Symptoms
    for sym in COMMON_SYMPTOMS:
        pattern = r'\b' + re.escape(sym) + r'\b'
        if re.search(pattern, text_lower):
            entities["symptoms"].add(sym.capitalize())

    # Rule matching for Diseases / Conditions
    for dis in COMMON_DISEASES:
        pattern = r'\b' + re.escape(dis) + r'\b'
        if re.search(pattern, text_lower):
            entities["diseases_conditions"].add(dis.capitalize())

    # Rule matching for Procedures
    for proc in COMMON_PROCEDURES:
        pattern = r'\b' + re.escape(proc) + r'\b'
        if re.search(pattern, text_lower):
            entities["procedures"].add(proc.capitalize())

    # Rule matching for Dates
    for d_match in REPORT_DATE_PATTERN.finditer(text):
        entities["dates"].add(d_match.group(1).strip())

    # Convert all sets to sorted lists for JSON serializability and determinism
    return {k: sorted(list(v)) for k, v in entities.items()}
