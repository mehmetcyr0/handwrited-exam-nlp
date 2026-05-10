/**
 * API kökü.
 * - Geliştirme (npm run dev): varsayılan boş → istekler /api, /health üzerinden gider;
 *   vite.config.js proxy bunları 127.0.0.1:8000'e iletir (CORS / port karışıklığı olmaz).
 * - Üretim build: doğrudan http://127.0.0.1:8000 (veya .env ile VITE_API_BASE=...).
 */
function apiBase() {
  const v = import.meta.env.VITE_API_BASE;
  if (typeof v === "string" && v.trim()) return v.trim().replace(/\/$/, "");
  if (import.meta.env.DEV) return "";
  return "http://127.0.0.1:8000";
}

export const API_BASE = apiBase();

/** Yardım metinleri ve /docs linki — backend her zaman bu adreste dinler */
export const BACKEND_ORIGIN = "http://127.0.0.1:8000";

function normalizeDetail(detail) {
  if (detail == null) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item.msg === "string") return item.msg;
        try {
          return JSON.stringify(item);
        } catch {
          return String(item);
        }
      })
      .filter(Boolean)
      .join(" · ");
  }
  if (typeof detail === "object" && typeof detail.message === "string") return detail.message;
  try {
    return JSON.stringify(detail);
  } catch {
    return String(detail);
  }
}

async function handle(res) {
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text || "Geçersiz yanıt" };
  }
  if (!res.ok) {
    const msg = normalizeDetail(data?.detail) ?? res.statusText;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
}

export async function uploadExam(file) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API_BASE}/api/upload`, { method: "POST", body: fd });
  return handle(res);
}

export async function extractText(uploadId) {
  const res = await fetch(`${API_BASE}/api/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ upload_id: uploadId }),
  });
  return handle(res);
}

export async function gradeExam(extractionId, answerKey, maxScore = 100) {
  const res = await fetch(`${API_BASE}/api/grade`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      extraction_id: extractionId,
      answer_key: answerKey,
      max_score: maxScore,
    }),
  });
  return handle(res);
}

export async function getResults(gradeId) {
  const res = await fetch(`${API_BASE}/api/results/${gradeId}`);
  return handle(res);
}

/** Backend ayakta mı (CORS + bağlantı testi) */
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return handle(res);
}
