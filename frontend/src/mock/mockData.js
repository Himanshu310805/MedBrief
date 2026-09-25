export const MOCK_SUMMARY_DATA = {
  patient_information: {
    patient_name: "John Doe (Synthetic)",
    age: "54",
    gender: "Male",
    report_date: "2026-09-10"
  },
  stats: {
    word_count: 305,
    sentence_count: 39,
    processing_time: 7.45,
    model_used: "distilbart-cnn-6-6",
    verification_rate: "100%"
  },
  symptoms: {
    content: "Chest pain, Chest tightness, Diaphoresis, Dyspnea, Edema, Exertional dyspnea, Nausea, Peripheral edema, Rales, Rhonchi, Shortness of breath, Syncope",
    verified: true
  },
  diagnosis_conditions: {
    content: "Acute coronary syndrome, Essential hypertension, Hyperlipidemia, Hypertension, Hypertensive heart disease, Hypertrophy, Left ventricular hypertrophy",
    verified: true
  },
  medications: {
    content: "Atorvastatin 20 mg, Lisinopril 10 mg",
    verified: true
  },
  lab_findings: {
    content: "BNP: 45 pg/mL, HDL 42 mg/dL, LDL 135 mg/dL, SpO2 97%, Total Cholesterol 215 mg/dL, Triglycerides 190 mg/dL, Troponin I: < 0.01 ng/mL, Blood Pressure: 138/86 mmHg, Heart Rate: 76 bpm",
    verified: true
  },
  procedures: {
    content: "Auscultation, Echocardiogram, Electrocardiogram, Stress test, Treadmill stress test",
    verified: true
  },
  other_observations: {
    content: "Vital Signs stable, Regular rate and rhythm, S1 and S2 present, Clear to auscultation bilaterally",
    verified: true
  },
  follow_up: {
    content: "Schedule an outpatient treadmill stress test within 2 weeks. Follow-up clinic appointment in 4 weeks or sooner if symptoms worsen.",
    verified: true
  },
  extractive_summary_text: "Patient reports shortness of breath on exertion and recurrent mild chest tightness over the past two weeks. The patient is a 54-year-old male with a history of essential hypertension and hyperlipidemia. Electrocardiogram (ECG): Normal sinus rhythm at 74 bpm. Exertional dyspnea secondary to mild hypertensive heart disease and hyperlipidemia. Initiate Atorvastatin 20 mg orally once daily for hyperlipidemia.",
  abstractive_summary_text: "The patient is a 54-year-old male with a history of essential hypertension and hyperlipidemia. He reports experiencing progressive exertional dyspnea when climbing stairs. Denies acute severe chest pain, radiation to jaw or arm, diaphoresis, nausea or syncope.",
  original_report_text: `PATIENT INFORMATION:
Patient Name: John Doe (Synthetic)
Age: 54 | Gender: Male | DOB: 1970-05-15
MRN: SYN-987654 | Date of Visit: 2026-09-10
Attending Physician: Dr. Jane Smith, MD (Cardiology)

CHIEF COMPLAINT:
Patient reports shortness of breath on exertion and recurrent mild chest tightness over the past two weeks.

CLINICAL HISTORY & PRESENT ILLNESS:
The patient is a 54-year-old male with a history of essential hypertension and hyperlipidemia. He reports experiencing progressive exertional dyspnea when climbing stairs. Denies acute severe chest pain, radiation to jaw or arm, diaphoresis, nausea, or syncope.

PHYSICAL EXAMINATION:
- Vital Signs: BP 138/86 mmHg, HR 76 bpm, RR 18/min, Temp 98.4°F, SpO2 97% on room air.
- Cardiovascular: Regular rate and rhythm. S1 and S2 present. No S3, S4, or murmurs.
- Respiratory: Clear to auscultation bilaterally. No wheezes, rales, or rhonchi.
- Extremities: No peripheral edema. Pulses intact 2+ bilaterally.

DIAGNOSTIC WORKUP & LAB RESULTS:
- Electrocardiogram (ECG): Normal sinus rhythm at 74 bpm. No acute ST-T wave changes.
- Troponin I: < 0.01 ng/mL (Normal)
- BNP: 45 pg/mL (Normal)
- Lipid Panel: Total Cholesterol 215 mg/dL, LDL 135 mg/dL, HDL 42 mg/dL, Triglycerides 190 mg/dL.
- Echocardiogram: Left ventricular ejection fraction (LVEF) 60%. Mild left ventricular hypertrophy. No regional wall motion abnormalities.

IMPRESSION / DIAGNOSIS:
1. Exertional dyspnea secondary to mild hypertensive heart disease and hyperlipidemia.
2. Acute coronary syndrome ruled out based on serial cardiac biomarkers and ECG.

TREATMENT PLAN & RECOMMENDATIONS:
1. Continue Lisinopril 10 mg orally once daily for blood pressure management.
2. Initiate Atorvastatin 20 mg orally once daily for hyperlipidemia.
3. Schedule an outpatient treadmill stress test within 2 weeks.
4. Dietary modifications: Low-sodium, heart-healthy Mediterranean diet.
5. Follow-up clinic appointment in 4 weeks or sooner if symptoms worsen.`,
  rouge_evaluation: {
    show: true,
    extractive_scores: {
      rouge1: { precision: 0.5833, recall: 0.4730, fmeasure: 0.5224 },
      rouge2: { precision: 0.3898, recall: 0.3151, fmeasure: 0.3485 },
      rougeL: { precision: 0.4500, recall: 0.3649, fmeasure: 0.4030 }
    },
    abstractive_scores: {
      rouge1: { precision: 0.5128, recall: 0.2703, fmeasure: 0.3540 },
      rouge2: { precision: 0.3684, recall: 0.1918, fmeasure: 0.2523 },
      rougeL: { precision: 0.4615, recall: 0.2432, fmeasure: 0.3186 }
    },
    comparison_note: "Extractive summary achieved a higher ROUGE-1 F1-score (0.5224 vs 0.3540) and recall (0.4730 vs 0.2703) compared to the abstractive summary. This reflects ROUGE's expected structural bias toward verbatim source sentence overlap."
  }
};
