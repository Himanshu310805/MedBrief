from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ExtractTextRequest(BaseModel):
    """Schema for plain text extraction and analysis requests."""
    text: str = Field(..., description="Raw text string to be cleaned and processed")


class ExtractResponse(BaseModel):
    """Schema for text extraction response."""
    success: bool = Field(..., description="Indicates whether extraction was successful")
    extracted_text: str = Field(..., description="Cleaned extracted text content")
    character_count: int = Field(..., description="Total character count of extracted text")
    word_count: int = Field(..., description="Total word count of extracted text")
    source_type: str = Field(..., description="Source of extraction ('pdf' or 'text')")
    warning: Optional[str] = Field(
        None,
        description="Warning message if text is empty or document requires OCR"
    )


class MedicalInfoResponse(BaseModel):
    """Schema for medical NLP entity and patient info analysis response."""
    success: bool = Field(..., description="Indicates whether analysis was successful")
    sentence_count: int = Field(..., description="Total sentence count after segmentation")
    normalized_text: str = Field(..., description="Text with expanded medical abbreviations")
    patient_info: Dict[str, Any] = Field(..., description="Extracted patient demographics & metadata")
    entities: Dict[str, Any] = Field(..., description="Categorized medical entities dictionary")
    warning: Optional[str] = Field(None, description="Optional warning message")


class ExtractiveSummaryRequest(BaseModel):
    """Schema for Extractive TextRank summary requests."""
    text: str = Field(..., description="Input text to summarize")
    num_sentences: int = Field(5, ge=1, le=15, description="Desired number of sentences in summary (1-15)")


class ExtractiveSummaryResponse(BaseModel):
    """Schema for Extractive TextRank summary response."""
    success: bool = Field(..., description="Indicates whether summarization was successful")
    summary_sentences: List[str] = Field(..., description="Selected top key sentences in chronological order")
    summary_text: str = Field(..., description="Joined full summary text")
    original_sentence_count: int = Field(..., description="Original total sentence count")
    summary_sentence_count: int = Field(..., description="Sentences included in summary")
    compression_ratio: float = Field(..., description="Compression ratio (summary length / original length)")
    warning: Optional[str] = Field(None, description="Warning or edge case note")


class AbstractiveSummaryRequest(BaseModel):
    """Schema for Abstractive Transformer summary requests."""
    text: str = Field(..., description="Input report text to summarize")
    max_length: int = Field(150, ge=20, le=500, description="Maximum token length of output summary")
    min_length: int = Field(40, ge=10, le=200, description="Minimum token length of output summary")


class AbstractiveSummaryResponse(BaseModel):
    """Schema for Abstractive Transformer summary response."""
    success: bool = Field(..., description="Indicates whether summarization was successful")
    abstractive_summary: str = Field(..., description="Generated abstractive summary text")
    chunks_processed: int = Field(..., description="Number of text chunks processed")
    model_used: str = Field(..., description="HuggingFace model name used")
    input_word_count: int = Field(..., description="Word count of input text")
    summary_word_count: int = Field(..., description="Word count of output summary")
    processing_time_seconds: float = Field(..., description="CPU inference execution time in seconds")
    warning: Optional[str] = Field(None, description="Optional warning message")


class LabResultItem(BaseModel):
    """Schema for an individual structured lab result row."""
    test_name: str = Field(..., description="Name of the clinical test")
    result: str = Field(..., description="Numeric or qualitative test result")
    unit: str = Field("", description="Measurement unit")
    reference_range: str = Field("", description="Reference normal range")
    flag: str = Field("Normal", description="Clinical flag ('High', 'Low', 'Normal')")


class StructuredSection(BaseModel):
    """Schema for a verified structured summary section."""
    content: str = Field(..., description="Text content for the clinical section or 'Not mentioned'")
    verified: bool = Field(..., description="Indicates whether section content was verified against original report text")


class StructuredSummaryResponse(BaseModel):
    """Schema for the full pipeline structured summary response."""
    success: bool = Field(..., description="Indicates whether full pipeline execution was successful")
    patient_information: Dict[str, Any] = Field(..., description="Patient demographic information dictionary")
    symptoms: StructuredSection = Field(..., description="Symptoms section content & verification status")
    diagnosis_conditions: StructuredSection = Field(..., description="Diagnosis & conditions section content & verification status")
    medications: StructuredSection = Field(..., description="Medications section content & verification status")
    lab_findings: StructuredSection = Field(..., description="Lab findings section content & verification status")
    lab_results_table: List[LabResultItem] = Field(default_factory=list, description="Structured table rows for lab findings")
    procedures: StructuredSection = Field(..., description="Procedures section content & verification status")
    other_observations: StructuredSection = Field(..., description="Other findings section content & verification status")
    follow_up: StructuredSection = Field(..., description="Follow-up section content & verification status")
    extractive_summary_text: str = Field(..., description="Verbatim Extractive TextRank summary text")
    abstractive_summary_text: str = Field(..., description="Paraphrased Abstractive Transformer summary text")


class RougeMetric(BaseModel):
    """Schema for individual precision, recall, and fmeasure metrics."""
    precision: float = Field(..., description="Precision score (0.0 to 1.0)")
    recall: float = Field(..., description="Recall score (0.0 to 1.0)")
    fmeasure: float = Field(..., description="F1-measure score (0.0 to 1.0)")


class RougeScores(BaseModel):
    """Schema for ROUGE-1, ROUGE-2, and ROUGE-L metric collection."""
    rouge1: RougeMetric = Field(..., description="ROUGE-1 unigram overlap scores")
    rouge2: RougeMetric = Field(..., description="ROUGE-2 bigram overlap scores")
    rougeL: RougeMetric = Field(..., description="ROUGE-L longest common subsequence scores")


class EvaluationRequest(BaseModel):
    """Schema for standalone ROUGE evaluation requests."""
    extractive_summary: str = Field(..., description="Extractive summary text")
    abstractive_summary: str = Field(..., description="Abstractive summary text")
    reference_summary: str = Field(..., description="Human gold-standard reference summary text")


class EvaluationResponse(BaseModel):
    """Schema for ROUGE evaluation response."""
    success: bool = Field(..., description="Indicates whether evaluation was successful")
    extractive_scores: RougeScores = Field(..., description="ROUGE scores for Extractive vs Reference summary")
    abstractive_scores: RougeScores = Field(..., description="ROUGE scores for Abstractive vs Reference summary")
    comparison_note: str = Field(..., description="Textual summary comparison observation note")


