const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const TOKEN_KEY = 'medbrief_token';

/**
 * Token Storage Helpers
 */
export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function removeStoredToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function getAuthHeaders(customHeaders = {}) {
  const token = getStoredToken();
  const headers = { ...customHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Helper to handle HTTP response errors
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'An unexpected server error occurred.';
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' 
          ? errorJson.detail 
          : JSON.stringify(errorJson.detail);
      }
    } catch {
      errorDetail = `Server returned HTTP ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

/**
 * Auth API 1: Sign Up
 * POST /api/auth/signup
 */
export async function signupUser(email, password, fullName) {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  const data = await handleResponse(response);
  if (data.access_token) {
    setStoredToken(data.access_token);
  }
  return data;
}

/**
 * Auth API 2: Log In
 * POST /api/auth/login
 */
export async function loginUser(email, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await handleResponse(response);
  if (data.access_token) {
    setStoredToken(data.access_token);
  }
  return data;
}

/**
 * Auth API 3: Get Current Authenticated User Profile
 * GET /api/auth/me
 */
export async function getMe() {
  const token = getStoredToken();
  if (!token) return null;
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: getAuthHeaders(),
    });
    const data = await handleResponse(response);
    return data.user;
  } catch (err) {
    removeStoredToken();
    return null;
  }
}

/**
 * Auth API 4: Log Out
 */
export function logoutUser() {
  removeStoredToken();
}

/**
 * 1. Extract text from uploaded PDF file
 * POST /api/extract-pdf
 */
export async function extractFromPdf(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/extract-pdf`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });

  return handleResponse(response);
}

/**
 * 1b. Extract text from uploaded image file (PNG/JPG/JPEG via OCR)
 * POST /api/extract-image
 */
export async function extractFromImage(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/extract-image`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });

  return handleResponse(response);
}

/**
 * 2. Extract & clean plain text
 * POST /api/extract-text
 */
export async function extractFromText(text) {
  const response = await fetch(`${API_BASE_URL}/api/extract-text`, {
    method: 'POST',
    headers: getAuthHeaders({
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify({ text }),
  });

  return handleResponse(response);
}

/**
 * 3. Analyze report end-to-end (NER + Extractive + Abstractive + Structured Assembly)
 * POST /api/analyze-full
 */
export async function analyzeFull(text) {
  const response = await fetch(`${API_BASE_URL}/api/analyze-full`, {
    method: 'POST',
    headers: getAuthHeaders({
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify({ text }),
  });

  return handleResponse(response);
}

/**
 * 4. Evaluate summary quality against reference summary using ROUGE
 * POST /api/evaluate
 */
export async function evaluateSummaries(extractiveSummary, abstractiveSummary, referenceSummary) {
  const response = await fetch(`${API_BASE_URL}/api/evaluate`, {
    method: 'POST',
    headers: getAuthHeaders({
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify({
      extractive_summary: extractiveSummary,
      abstractive_summary: abstractiveSummary,
      reference_summary: referenceSummary,
    }),
  });

  return handleResponse(response);
}

/**
 * 5. Download structured summary as PDF
 * POST /api/download-report
 */
export async function downloadReport(reportData) {
  const response = await fetch(`${API_BASE_URL}/api/download-report`, {
    method: 'POST',
    headers: getAuthHeaders({
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify(reportData),
  });

  if (!response.ok) {
    let errorDetail = 'Failed to download report PDF.';
    try {
      const errorJson = await response.json();
      if (errorJson.detail) errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
    } catch {}
    throw new Error(errorDetail);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;

  const contentDisposition = response.headers.get('Content-Disposition');
  let filename = 'medbrief_clinical_report.pdf';
  if (contentDisposition && contentDisposition.includes('filename=')) {
    filename = contentDisposition.split('filename=')[1].trim().replace(/^["']|["']$/g, '');
  }

  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

/**
 * 6. Get Report History for Authenticated User
 * GET /api/reports
 */
export async function getUserReports() {
  const response = await fetch(`${API_BASE_URL}/api/reports`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}

/**
 * Health check endpoint
 * GET /api/health
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  return handleResponse(response);
}
