import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { BACKEND_ORIGIN, uploadExam, extractText, gradeExam, checkHealth } from "../api.js";

function friendlyFetchError(err) {
  const m = err?.message || String(err);
  if (
    m === "Failed to fetch" ||
    /networkerror|failed to load|load failed|network request failed/i.test(m)
  ) {
    return [
      "API sunucusuna bağlanılamadı (ağ hatası).",
      `Backend şu adreste çalışmalı: ${BACKEND_ORIGIN}`,
      "Çözüm: Proje kökünde run-all.cmd veya backend klasöründe start-api.cmd çalıştırın. PowerShell’de (backend içindeyken): .venv\\Scripts\\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 — Not: Sadece «uvicorn» yazmayın; PATH’te olmayabilir.",
      "Kontrol: tarayıcıda " + BACKEND_ORIGIN + "/docs açılmalı.",
    ].join(" ");
  }
  return m;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [answerKey, setAnswerKey] = useState("");
  const [maxScore, setMaxScore] = useState(100);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [lastExtract, setLastExtract] = useState(null);
  const [backendOk, setBackendOk] = useState(null);

  useEffect(() => {
    let cancelled = false;
    checkHealth()
      .then(() => {
        if (!cancelled) setBackendOk(true);
      })
      .catch(() => {
        if (!cancelled) setBackendOk(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onGrade() {
    setError("");
    setStatus("");
    if (!file) {
      setError("Önce sınav görselini veya PDF’ini yükleyin.");
      return;
    }
    if (!answerKey.trim()) {
      setError("Cevap anahtarı metnini girin.");
      return;
    }

    setBusy(true);
    try {
      setStatus("Dosya yükleniyor…");
      const up = await uploadExam(file);
      setStatus("Görüntü işleniyor ve metin çıkarılıyor (OCR)…");
      const ex = await extractText(up.id);
      setLastExtract(ex);
      setStatus("Anlamsal benzerlik ve puanlama hesaplanıyor…");
      const gr = await gradeExam(ex.extraction_id, answerKey.trim(), maxScore);
      setStatus("Tamamlandı.");
      navigate(`/sonuc/${gr.grade_id}`);
    } catch (e) {
      setError(friendlyFetchError(e));
      setStatus("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-10">
      {backendOk === false && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          <strong>Backend görünmüyor.</strong>{" "}
          <a
            href={`${BACKEND_ORIGIN}/docs`}
            target="_blank"
            rel="noreferrer"
            className="text-accent underline font-medium"
          >
            {BACKEND_ORIGIN}/docs
          </a>{" "}
          açılmıyorsa API çalışmıyordur. <code className="bg-amber-100/80 px-1 rounded">backend\start-api.cmd</code>{" "}
          çalıştırın veya <code className="bg-amber-100/80 px-1 rounded">python -m uvicorn</code> kullanın (tek başına{" "}
          <code className="bg-amber-100/80 px-1 rounded">uvicorn</code> Windows’ta genelde tanınmaz).
        </div>
      )}

      <section className="rounded-2xl bg-white border border-slate-200/90 shadow-sm shadow-slate-200/50 p-8 space-y-2">
        <h2 className="text-2xl font-semibold text-ink-950">Değerlendirme paneli</h2>
        <p className="text-ink-700 max-w-2xl">
          El yazısı sınav görseli (JPG, PNG) veya PDF yükleyin; cevap anahtarını yazın. Sistem
          görüntüyü iyileştirir, PaddleOCR ile metni okur ve cümle gömüleriyle anlamsal benzerlik
          hesaplar — kelime eşleştirmesi kullanılmaz.
        </p>
      </section>

      <div className="grid md:grid-cols-2 gap-8">
        <section className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-4 shadow-sm">
          <h3 className="font-semibold text-ink-950">1. Sınav dosyası</h3>
          <label className="block">
            <span className="text-sm text-ink-700 mb-2 block">Görsel veya PDF</span>
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
              className="block w-full text-sm text-ink-700 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-accent file:text-white file:font-medium hover:file:bg-accent-dim cursor-pointer"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              disabled={busy}
            />
          </label>
          {file && (
            <p className="text-xs text-ink-700 truncate" title={file.name}>
              Seçili: {file.name}
            </p>
          )}
        </section>

        <section className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-4 shadow-sm">
          <h3 className="font-semibold text-ink-950">2. Cevap anahtarı</h3>
          <textarea
            className="w-full min-h-[160px] rounded-xl border border-slate-200 bg-paper-50 px-3 py-2 text-sm text-ink-950 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
            placeholder={`Örnek:\n1. Fotosentez bitkilerde glukoz üretir.\n2. Mitokondri enerji üretir.`}
            value={answerKey}
            onChange={(e) => setAnswerKey(e.target.value)}
            disabled={busy}
          />
          <div className="flex items-center gap-3">
            <label className="text-sm text-ink-700 shrink-0">Maks. puan</label>
            <input
              type="number"
              min={1}
              max={1000}
              className="w-24 rounded-lg border border-slate-200 px-2 py-1 text-sm"
              value={maxScore}
              onChange={(e) => setMaxScore(Number(e.target.value) || 100)}
              disabled={busy}
            />
          </div>
        </section>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <button
          type="button"
          onClick={onGrade}
          disabled={busy}
          className="inline-flex items-center justify-center rounded-xl bg-accent px-6 py-3 text-white font-semibold shadow-lg shadow-accent/25 hover:bg-accent-dim disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {busy ? "İşleniyor…" : "Değerlendirmeyi başlat"}
        </button>
        {status && <p className="text-sm text-ink-700">{status}</p>}
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {lastExtract && !busy && (
        <details className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
          <summary className="cursor-pointer font-medium text-ink-950">Son OCR önizlemesi</summary>
          <pre className="mt-3 whitespace-pre-wrap text-ink-700 max-h-64 overflow-auto">
            {lastExtract.extracted_text || "(boş)"}
          </pre>
        </details>
      )}
    </div>
  );
}
