"""
Abstractive Summarization Service using HuggingFace Transformers.

Abstractive summarization synthesizes and generates NEW sentences in the model's own words,
unlike Extractive summarization (Stage 4) which only extracts verbatim original sentences.
This service utilizes a pretrained sequence-to-sequence transformer model (sshleifer/distilbart-cnn-6-6),
which processes document tokens through encoder-decoder attention layers to produce concise,
paraphrased clinical narratives.
"""

import time
import logging
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from app.services.preprocessing import segment_sentences

logger = logging.getLogger("uvicorn")

MODEL_NAME = "sshleifer/distilbart-cnn-6-6"
# device_id = -1 forces CPU execution ("cpu"). Change device_id to 0 (or "cuda") if a CUDA GPU is available.
device_id = -1
device_str = "cuda" if (device_id >= 0 and torch.cuda.is_available()) else "cpu"

model = None
tokenizer = None
MODEL_LOAD_ERROR = None

def _get_model_and_tokenizer():
    """Lazy loads transformer model and tokenizer on first invocation."""
    global model, tokenizer, MODEL_LOAD_ERROR
    if model is None and MODEL_LOAD_ERROR is None:
        try:
            print(f"Loading Abstractive Summarization Transformer Model '{MODEL_NAME}' on {device_str.upper()}...")
            start_dl = time.time()
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device_str)
            dl_time = round(time.time() - start_dl, 2)
            print(f"Successfully loaded model '{MODEL_NAME}' in {dl_time}s.")
        except Exception as e:
            MODEL_LOAD_ERROR = str(e)
            print(f"Failed to load transformer model '{MODEL_NAME}': {MODEL_LOAD_ERROR}")
    return model, tokenizer


def chunk_text_for_model(text: str, max_tokens: int = 1000) -> list[str]:
    """
    Splits long input text into sentence-aligned chunks that fit within model token limits.

    Args:
        text (str): Input text document.
        max_tokens (int): Maximum allowed tokens per chunk (default 1000 for BART max limit of 1024).

    Returns:
        list[str]: List of text chunk strings.
    """
    sentences = segment_sentences(text)
    if not sentences:
        return []

    if tokenizer is None:
        # Fallback word-based chunking if tokenizer is unavailable
        words = text.split()
        return [" ".join(words[i:i+500]) for i in range(0, len(words), 500)]

    chunks = []
    current_chunk = []
    current_token_count = 0

    for sentence in sentences:
        # Accurately count tokens using the model's tokenizer
        sentence_tokens = len(tokenizer.encode(sentence, add_special_tokens=False))

        if current_token_count + sentence_tokens > max_tokens and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_token_count = sentence_tokens
        else:
            current_chunk.append(sentence)
            current_token_count += sentence_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def generate_abstractive_summary(text: str, max_length: int = 150, min_length: int = 40) -> dict:
    """
    Generates an abstractive summary using the transformer model.

    Args:
        text (str): Input report text.
        max_length (int): Maximum token length for the output summary.
        min_length (int): Minimum token length for the output summary.

    Returns:
        dict: Abstractive summary response metadata dictionary.
    """
    curr_model, curr_tokenizer = _get_model_and_tokenizer()

    if curr_model is None or curr_tokenizer is None:
        return {
            "abstractive_summary": "",
            "chunks_processed": 0,
            "model_used": MODEL_NAME,
            "input_word_count": len(text.split()),
            "summary_word_count": 0,
            "warning": f"Model failed to load. Check internet connection for initial model download. Error: {MODEL_LOAD_ERROR}"
        }

    input_words = text.split()
    input_word_count = len(input_words)

    if input_word_count == 0:
        return {
            "abstractive_summary": "",
            "chunks_processed": 0,
            "model_used": MODEL_NAME,
            "input_word_count": 0,
            "summary_word_count": 0,
            "warning": "Input text is empty."
        }

    warning_msg = None
    if input_word_count < 30:
        warning_msg = "Input text is very short (<30 words). Abstractive summarization may produce repetitive or low-quality phrasing on extremely brief text."

    # Chunk text to respect max token limits (~1000 tokens per chunk for BART max limit of 1024)
    chunks = chunk_text_for_model(text, max_tokens=1000)
    summarized_chunks = []

    for chunk in chunks:
        chunk_word_count = len(chunk.split())
        # Adjust max_length and min_length dynamically for shorter chunks
        adj_max = min(max_length, max(20, int(chunk_word_count * 0.7)))
        adj_min = min(min_length, max(10, int(adj_max * 0.4)))

        try:
            inputs = tokenizer(chunk, max_length=1024, return_tensors="pt", truncation=True).to(device_str)
            summary_ids = model.generate(
                inputs["input_ids"],
                max_length=adj_max,
                min_length=adj_min,
                num_beams=4,
                early_stopping=True,
                no_repeat_ngram_size=3
            )
            summary_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
            summarized_chunks.append(summary_text)
        except Exception as err:
            logger.error(f"Error during chunk abstractive summarization: {err}")
            summarized_chunks.append(chunk)

    # NOTE / LIMITATION: If multiple chunks exist, we concatenate their summaries into one final summary text.
    # True long-document abstractive summarization uses multi-stage hierarchical or cross-attention models.
    # Simple concatenation is an acceptable simplification for this mini-project.
    final_summary = " ".join(summarized_chunks)
    summary_word_count = len(final_summary.split())

    return {
        "abstractive_summary": final_summary,
        "chunks_processed": len(chunks),
        "model_used": MODEL_NAME,
        "input_word_count": input_word_count,
        "summary_word_count": summary_word_count,
        "warning": warning_msg
    }
