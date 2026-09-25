# MedBrief Backend

FastAPI backend service for MedBrief Medical Report Summarizer.

## System Dependencies (OCR & PDF Processing)

MedBrief supports scanned PDF and image OCR processing using **Tesseract OCR** and **Poppler**.

### Windows Installation
1. **Tesseract OCR**: Download and run the Windows installer from [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki). Add `C:\Program Files\Tesseract-OCR` to your system environment `PATH`.
2. **Poppler**: Download pre-compiled binaries from [poppler-windows releases](https://github.com/oschwartz10612/poppler-windows/releases). Extract and add the `bin/` directory (e.g., `C:\poppler\Library\bin`) to your system environment `PATH`.
3. Verify in a fresh terminal:
   ```cmd
   tesseract --version
   pdftoppm -v
   ```

### macOS Installation
```bash
brew install tesseract poppler
```

### Linux Installation
```bash
sudo apt update
sudo apt install tesseract-ocr poppler-utils
```

---

## Setup Instructions

### 1. Create a Virtual Environment
From the `backend` directory:

```bash
# On Windows (PowerShell / Command Prompt)
python -m venv venv
venv\Scripts\activate

# On Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Run the Server
```bash
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

---

## API Endpoints

### 1. Health Check
- **Method:** `GET`
- **Path:** `/api/health`
- **Response:**
  ```json
  {
    "status": "ok",
    "service": "MedBrief backend"
  }
  ```

---

### 2. Extract Text from Plain Text
- **Method:** `POST`
- **Path:** `/api/extract-text`
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "text": "PATIENT NAME: John Doe\nDIAGNOSIS: Acute bronchitis."
  }
  ```
- **Response Format:**
  ```json
  {
    "success": true,
    "extracted_text": "PATIENT NAME: John Doe\nDIAGNOSIS: Acute bronchitis.",
    "character_count": 52,
    "word_count": 7,
    "source_type": "text",
    "warning": null
  }
  ```

---

### 3. Extract Text from PDF File
- **Method:** `POST`
- **Path:** `/api/extract-pdf`
- **Content-Type:** `multipart/form-data`
- **Form Field:** `file` (PDF document, max size 10MB)
- **Note:** Supports selectable text PDFs and automatically falls back to OCR via Poppler + Tesseract for scanned image-only PDFs.
- **Response Format:**
  ```json
  {
    "success": true,
    "extracted_text": "MEDBRIEF SYNTHETIC MEDICAL REPORT...",
    "character_count": 1642,
    "word_count": 287,
    "source_type": "pdf",
    "warning": null
  }
  ```

---

### 4. Extract Text from Image File (OCR)
- **Method:** `POST`
- **Path:** `/api/extract-image`
- **Content-Type:** `multipart/form-data`
- **Form Field:** `file` (Image file: .png, .jpg, .jpeg, max size 10MB)
- **Description:** Runs OpenCV adaptive thresholding, deskewing, and mild denoising before Tesseract OCR, followed by document noise filtering.
- **Response Format:**
  ```json
  {
    "success": true,
    "extracted_text": "COMPLETE BLOOD COUNT (CBC)\nHEMOGLOBIN: 14.2 g/dL...",
    "character_count": 850,
    "word_count": 120,
    "source_type": "image",
    "warning": null
  }
  ```

---

### 5. Extract Medical Entities & Patient Info
- **Method:** `POST`
- **Path:** `/api/extract-entities`
- **Content-Type:** `application/json`

---

### 6. Extractive Summarization (TextRank)
- **Method:** `POST`
- **Path:** `/api/summarize-extractive`

---

### 7. Abstractive Summarization (HuggingFace Transformer)
- **Method:** `POST`
- **Path:** `/api/summarize-abstractive`

---

### 8. Full Pipeline Structured Summarization (Primary Endpoint)
- **Method:** `POST`
- **Path:** `/api/analyze-full`

---

### 9. ROUGE Evaluation (Optional Standalone Endpoint)
- **Method:** `POST`
- **Path:** `/api/evaluate`

---

## Known Limitations & Best Practices

1. **OCR Quality Dependency**: OCR accuracy relies heavily on image resolution, lighting, and contrast. Preprocessing (deskewing, adaptive thresholding) improves results, but very low-resolution or blurry photos may have lower accuracy.
2. **Handwritten Text**: Handwritten notes are not supported by the current Tesseract configuration.
3. **Complex Layouts & Tables**: Multi-column documents or non-standard tabular structures are converted to raw text streams and processed by downstream narrative generators.
