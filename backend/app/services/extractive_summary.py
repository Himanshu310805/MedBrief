"""
TextRank Extractive Summarization Service.

TextRank is an unsupervised graph-based ranking algorithm adapted from Google's PageRank.
In sentence extraction, individual sentences from a document are represented as nodes in a graph,
and edges between nodes are weighted based on inter-sentence textual similarity (TF-IDF cosine similarity).
The PageRank algorithm iteratively computes an importance score for each sentence based on its connections,
allowing the system to select the most central, informative sentences without relying on machine learning training data.
"""

import re
import numpy as np
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.preprocessing import segment_sentences

# Section headers or banner titles to exclude from TextRank candidate selection
# Matches standalone titles like "DIAGNOSIS:", "CHIEF COMPLAINT:", "PATIENT INFORMATION"
HEADER_NOISE_PATTERNS = re.compile(
    r'^(?:PATIENT INFORMATION|CHIEF COMPLAINT|CLINICAL HISTORY|PHYSICAL EXAMINATION|'
    r'DIAGNOSTIC WORKUP|LAB RESULTS|IMPRESSION|DIAGNOSIS|TREATMENT PLAN|RECOMMENDATIONS|'
    r'MEDBRIEF SYNTHETIC MEDICAL REPORT|TEST DATA ONLY)\s*[:\-]?\s*$',
    re.IGNORECASE
)


def is_meaningful_sentence(sentence: str) -> bool:
    """Checks if a sentence is a meaningful candidate for summary (not a standalone section header)."""
    s_clean = sentence.strip()
    if not s_clean or len(s_clean) < 8:
        return False
    # If line is short and ends with colon, it's a section title header (e.g. "DIAGNOSIS:")
    if s_clean.endswith(':') and len(s_clean.split()) <= 4:
        return False
    if HEADER_NOISE_PATTERNS.match(s_clean):
        return False
    return True


def build_similarity_matrix(sentences: list[str]) -> np.ndarray:
    """
    Computes a pairwise cosine similarity matrix for a list of sentences using TF-IDF.

    Args:
        sentences (list[str]): List of sentence strings.

    Returns:
        np.ndarray: Square matrix of shape (N, N) containing sentence similarity scores.
    """
    num_sentences = len(sentences)
    if num_sentences == 0:
        return np.zeros((0, 0))

    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(sentences)
        sim_matrix = cosine_similarity(tfidf_matrix)
    except ValueError:
        # Occurs if sentences contain only stop words or punctuation
        sim_matrix = np.zeros((num_sentences, num_sentences))

    # Remove self-similarity by setting diagonal to zero
    np.fill_diagonal(sim_matrix, 0)
    return sim_matrix


def rank_sentences_textrank(sentences: list[str]) -> list[tuple[int, float]]:
    """
    Ranks sentences using the TextRank graph-based algorithm.

    Args:
        sentences (list[str]): List of document sentences.

    Returns:
        list[tuple[int, float]]: List of (original_sentence_index, rank_score) tuples sorted by score descending.
    """
    num_sentences = len(sentences)
    if num_sentences == 0:
        return []
    if num_sentences == 1:
        return [(0, 1.0)]

    sim_matrix = build_similarity_matrix(sentences)

    # Build NetworkX Graph
    graph = nx.Graph()
    for i in range(num_sentences):
        graph.add_node(i)

    # Add weighted edges between sentences
    for i in range(num_sentences):
        for j in range(i + 1, num_sentences):
            weight = float(sim_matrix[i][j])
            if weight > 0:
                graph.add_edge(i, j, weight=weight)

    # Calculate PageRank scores
    try:
        if graph.number_of_edges() == 0:
            scores = {i: 1.0 / num_sentences for i in range(num_sentences)}
        else:
            scores = nx.pagerank(graph, weight='weight', max_iter=200)
    except Exception:
        scores = {i: 1.0 / num_sentences for i in range(num_sentences)}

    # Sort sentence indices by score descending
    ranked_sentences = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return ranked_sentences


def generate_extractive_summary(text: str, num_sentences: int = 5) -> dict:
    """
    Generates an extractive text summary using TextRank.
    Selected sentences are re-ordered chronologically as they appeared in the original report.

    Args:
        text (str): Input medical report text.
        num_sentences (int): Target number of sentences for the summary (default 5).

    Returns:
        dict: Summary metadata dictionary.
    """
    # 1. Segment sentences
    all_sentences = segment_sentences(text)
    total_sentences = len(all_sentences)

    if total_sentences == 0:
        return {
            "summary_sentences": [],
            "summary_text": "",
            "original_sentence_count": 0,
            "summary_sentence_count": 0,
            "compression_ratio": 0.0,
            "warning": "Input text is empty."
        }

    # Filter candidate sentences for ranking
    candidate_indices = [i for i, s in enumerate(all_sentences) if is_meaningful_sentence(s)]
    candidate_sentences = [all_sentences[i] for i in candidate_indices]

    # If no candidate sentences pass filter (or very short document), fallback to all sentences
    if not candidate_sentences:
        candidate_indices = list(range(total_sentences))
        candidate_sentences = all_sentences

    # 2. Edge case: if document has fewer or equal sentences than requested num_sentences
    if len(candidate_sentences) <= num_sentences:
        summary_sentences = candidate_sentences
        summary_text = " ".join(summary_sentences)
        compression_ratio = round(len(summary_text) / max(len(text), 1), 2)
        return {
            "summary_sentences": summary_sentences,
            "summary_text": summary_text,
            "original_sentence_count": total_sentences,
            "summary_sentence_count": len(summary_sentences),
            "compression_ratio": compression_ratio,
            "warning": f"Input text contains only {len(candidate_sentences)} candidate sentences (<= requested {num_sentences}). Returning full candidate text."
        }

    # 3. Rank candidate sentences using TextRank
    ranked_tuples = rank_sentences_textrank(candidate_sentences)

    # 4. Pick top num_sentences highest scoring candidate sentence indices
    top_cand_indices = [cand_idx for cand_idx, score in ranked_tuples[:num_sentences]]

    # Map back to original document sentence indices and sort chronologically
    top_orig_indices = sorted([candidate_indices[i] for i in top_cand_indices])

    # 5. Assemble summary text in original chronological order
    summary_sentences = [all_sentences[idx] for idx in top_orig_indices]
    summary_text = " ".join(summary_sentences)
    compression_ratio = round(len(summary_text) / max(len(text), 1), 2)

    return {
        "summary_sentences": summary_sentences,
        "summary_text": summary_text,
        "original_sentence_count": total_sentences,
        "summary_sentence_count": len(summary_sentences),
        "compression_ratio": compression_ratio,
        "warning": None
    }
