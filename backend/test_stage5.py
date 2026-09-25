import time
from app.services.abstractive_summary import generate_abstractive_summary
from app.services.extractive_summary import generate_extractive_summary

with open('sample_reports/sample_report_01.txt', 'r', encoding='utf-8') as f:
    text = f.read()

t0 = time.time()
abs_res = generate_abstractive_summary(text, max_length=150, min_length=40)
t1 = time.time()

ext_res = generate_extractive_summary(text, num_sentences=4)

print("=== STAGE 5 TEST RESULTS ===")
print(f"Abstractive Processing Time: {round(t1 - t0, 2)} seconds")
print(f"Model Used: {abs_res['model_used']}")
print(f"Input Word Count: {abs_res['input_word_count']}")
print(f"Summary Word Count: {abs_res['summary_word_count']}")
print(f"Chunks Processed: {abs_res['chunks_processed']}")
print(f"Warning: {abs_res['warning']}")

print("\n--- ABSTRACTIVE SUMMARY ---")
print(abs_res['abstractive_summary'])

print("\n--- EXTRACTIVE SUMMARY (STAGE 4) ---")
print(ext_res['summary_text'])
