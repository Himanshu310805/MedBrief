"""
ROUGE Evaluation Service Module for MedBrief.

ACADEMIC & EVALUATION NOTE:
ROUGE (Recall-Oriented Understudy for Gisting Evaluation) measures lexical n-gram
overlap between a candidate generated summary and a human-written reference summary.
- ROUGE-1: Unigram overlap (vocabulary matching).
- ROUGE-2: Bigram overlap (word pair sequence matching).
- ROUGE-L: Longest Common Subsequence (sentence structure matching).

KNOWN METRIC LIMITATIONS:
ROUGE evaluates exact surface word overlap rather than semantic intent or clinical paraphrasing.
Consequently, extractive summaries (which reuse exact verbatim sentences from the source document)
frequently achieve higher ROUGE scores than abstractive summaries, even when the abstractive summary
is more fluent or syntactically natural. ROUGE should be interpreted as an automated proxy metric
alongside qualitative clinical evaluation.
"""

from typing import Dict, Any
from rouge_score import rouge_scorer


def compute_rouge_scores(generated_summary: str, reference_summary: str) -> Dict[str, Dict[str, float]]:
    """
    Computes ROUGE-1, ROUGE-2, and ROUGE-L metrics for a generated summary against a reference text.

    Args:
        generated_summary (str): The candidate summary string to evaluate.
        reference_summary (str): The gold-standard human reference summary string.

    Returns:
        dict: Nested dictionary containing precision, recall, and fmeasure for rouge1, rouge2, and rougeL
              rounded to 4 decimal places.
    """
    if not generated_summary or not reference_summary:
        empty_metric = {"precision": 0.0, "recall": 0.0, "fmeasure": 0.0}
        return {
            "rouge1": empty_metric,
            "rouge2": empty_metric,
            "rougeL": empty_metric
        }

    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(target=reference_summary, prediction=generated_summary)

    formatted_scores = {}
    for metric, score in scores.items():
        formatted_scores[metric] = {
            "precision": round(score.precision, 4),
            "recall": round(score.recall, 4),
            "fmeasure": round(score.fmeasure, 4)
        }

    return formatted_scores


def evaluate_summaries(
    extractive_summary: str,
    abstractive_summary: str,
    reference_summary: str
) -> Dict[str, Any]:
    """
    Evaluates both Extractive and Abstractive summaries against a user-provided reference summary.

    Args:
        extractive_summary (str): TextRank extractive summary text.
        abstractive_summary (str): Transformer abstractive summary text.
        reference_summary (str): User-provided gold-standard reference summary text.

    Returns:
        dict: Evaluation results containing extractive_scores, abstractive_scores, and a comparison_note.
    """
    ext_scores = compute_rouge_scores(extractive_summary, reference_summary)
    abs_scores = compute_rouge_scores(abstractive_summary, reference_summary)

    ext_f1 = ext_scores["rouge1"]["fmeasure"]
    abs_f1 = abs_scores["rouge1"]["fmeasure"]

    ext_rec = ext_scores["rouge1"]["recall"]
    abs_rec = abs_scores["rouge1"]["recall"]

    # Factual comparison note without biased qualitative assertions
    if ext_f1 > abs_f1:
        note = (
            f"Extractive summary achieved a higher ROUGE-1 F1-score ({ext_f1:.4f} vs {abs_f1:.4f}) "
            f"and recall ({ext_rec:.4f} vs {abs_rec:.4f}) compared to the abstractive summary. "
            "This reflects ROUGE's expected structural bias toward verbatim source sentence overlap."
        )
    elif abs_f1 > ext_f1:
        note = (
            f"Abstractive summary achieved a higher ROUGE-1 F1-score ({abs_f1:.4f} vs {ext_f1:.4f}) "
            f"and recall ({abs_rec:.4f} vs {ext_rec:.4f}) compared to the extractive summary, "
            "demonstrating strong alignment with the reference summary vocabulary."
        )
    else:
        note = (
            f"Extractive and Abstractive summaries achieved identical ROUGE-1 F1-scores ({ext_f1:.4f})."
        )

    return {
        "success": True,
        "extractive_scores": ext_scores,
        "abstractive_scores": abs_scores,
        "comparison_note": note
    }
