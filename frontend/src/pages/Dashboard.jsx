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

function IconCloud({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M7 18a4 4 0 01-1.05-7.87 3.5 3.5 0 016.77-1.04A4 4 0 0117 18H7z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M12 11V7m0 0l-2 2m2-2l2 2"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconDoc({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M14 2H8a2 2 0 00-2 2v16a2 2 0 002 2h8a2 2 0 002-2V7l-5-5z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path d="M14 2v5h5M10 13h4M10 17h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function IconSpark({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 3l1.09 4.26L17 8.27l-3.18 2.55L15.18 15 12 12.77 8.82 15l1.36-4.18L7 8.27l3.91-.98L12 3z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

const stepsBusy = ["Dosya yükleniyor", "OCR ile metin çıkarılıyor", "Benzerlik ve puan hesaplanıyor"];

export default function Dashboard() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [answerKey, setAnswerKey] = useState("");
  const [maxScore, setMaxScore] = useState(100);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [busyStep, setBusyStep] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [lastExtract, setLastExtract] = useState(null);
  const [backendOk, setBackendOk] = useState(null);
  const [healthTick, setHealthTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setBackendOk(null);
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
  }, [healthTick]);

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
    setBusyStep(0);
    try {
      setStatus("Dosya yükleniyor…");
      const up = await uploadExam(file);
      setStatus("Görüntü işleniyor ve metin çıkarılıyor (OCR)…");
      setBusyStep(1);
      const ex = await extractText(up.id);
      setLastExtract(ex);
      setStatus("Anlamsal ve kelime benzerliği ile puanlama…");
      setBusyStep(2);
      const gr = await gradeExam(ex.extraction_id, answerKey.trim(), maxScore);
      setStatus("Tamamlandı.");
      navigate(`/sonuc/${gr.grade_id}`);
    } catch (e) {
      setError(friendlyFetchError(e));
      setStatus("");
    } finally {
      setBusy(false);
      setBusyStep(0);
    }
  }

  return (
    <div className="relative max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-14 animate-fade-in">
      {/* API durumu */}
      <div className="mb-10">
        {backendOk === false && (
          <div className="rounded-2xl border border-amber-200/90 bg-gradient-to-r from-amber-50 to-orange-50/80 px-4 sm:px-5 py-4 shadow-card flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
            <div className="text-sm text-amber-950 leading-relaxed">
              <span className="font-semibold">Backend erişilemiyor.</span>{" "}
              <a
                href={`${BACKEND_ORIGIN}/docs`}
                target="_blank"
                rel="noreferrer"
                className="text-accent font-semibold underline decoration-accent/40 underline-offset-2 hover:decoration-accent"
              >
                {BACKEND_ORIGIN}/docs
              </a>{" "}
              açılmıyorsa API kapalıdır.{" "}
              <code className="rounded-md bg-amber-100/90 px-1.5 py-0.5 text-xs font-mono">run-all.cmd</code> veya{" "}
              <code className="rounded-md bg-amber-100/90 px-1.5 py-0.5 text-xs font-mono">start-api.cmd</code>
            </div>
            <button
              type="button"
              onClick={() => setHealthTick((t) => t + 1)}
              className="shrink-0 rounded-xl border border-amber-300/80 bg-white px-4 py-2 text-xs font-semibold text-amber-950 shadow-sm hover:bg-amber-50 transition-colors"
            >
              Yeniden dene
            </button>
          </div>
        )}
        {backendOk === null && (
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200/90 bg-white/90 px-4 py-2 text-xs font-medium text-ink-600 shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent/40 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
            </span>
            API bağlantısı kontrol ediliyor…
          </div>
        )}
        {backendOk === true && (
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200/90 bg-emerald-50/90 px-4 py-2 text-xs font-semibold text-emerald-800 shadow-sm">
            <span className="h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-emerald-200" />
            API hazır
          </div>
        )}
      </div>

      {/* Hero */}
      <div className="mb-12 text-center sm:text-left sm:flex sm:items-end sm:justify-between gap-8">
        <div className="max-w-2xl space-y-4">
          <h2 className="text-3xl sm:text-4xl font-bold text-ink-950 tracking-tight leading-[1.15]">
            El yazısı sınavları{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-cyan-600">otomatik puanlayın</span>
          </h2>
          <p className="text-ink-600 text-[15px] leading-relaxed font-medium">
            Görüntü veya PDF yükleyin, cevap anahtarını girin. Çoklu OCR motoru metni çıkarır; anlamsal ve kelime
            benzerliği birleşik skora dönüşür — tüm işlem yerelde çalışır.
          </p>
        </div>
        <div className="hidden sm:flex flex-col gap-2 text-right shrink-0">
          <div className="flex items-center justify-end gap-2 text-xs font-semibold text-ink-500 uppercase tracking-wider">
            Özellikler
          </div>
          <div className="flex flex-wrap justify-end gap-2">
            {[
              { Icon: IconCloud, label: "Çoklu OCR" },
              { Icon: IconSpark, label: "MiniLM / TF‑IDF" },
              { Icon: IconDoc, label: "PDF · görsel" },
            ].map(({ Icon, label }) => (
              <span
                key={label}
                className="inline-flex items-center gap-1.5 rounded-full border border-slate-200/90 bg-white/90 px-3 py-1.5 text-xs font-semibold text-ink-700 shadow-sm"
              >
                <Icon className="h-3.5 w-3.5 text-accent" />
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Mobil özellik çipleri */}
      <div className="flex sm:hidden flex-wrap gap-2 mb-10">
        {["Çoklu OCR", "Anlamsal + kelime", "PDF"].map((label) => (
          <span
            key={label}
            className="rounded-full border border-slate-200/90 bg-white/90 px-3 py-1 text-[11px] font-semibold text-ink-600 shadow-sm"
          >
            {label}
          </span>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6 lg:gap-8">
        {/* Dosya */}
        <section className="group relative rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-card hover:shadow-card-hover transition-shadow duration-300">
          <div className="absolute top-6 right-6 sm:top-8 sm:right-8 flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-xs font-bold text-ink-500 tabular-nums">
            01
          </div>
          <div className="flex items-start gap-4 mb-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10 text-accent">
              <IconCloud className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-ink-950 tracking-tight">Sınav dosyası</h3>
              <p className="text-sm text-ink-600 mt-0.5 font-medium">JPG, PNG veya PDF (ilk sayfa)</p>
            </div>
          </div>
          <label className="block cursor-pointer">
            <div
              onDragEnter={(e) => {
                e.preventDefault();
                if (!busy) setDragOver(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                if (!e.currentTarget.contains(e.relatedTarget)) setDragOver(false);
              }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                if (busy) return;
                const f = e.dataTransfer.files?.[0];
                if (f) setFile(f);
              }}
              className={`rounded-xl border-2 border-dashed px-5 py-10 text-center transition-colors ${
                file
                  ? "border-accent/40 bg-accent/5"
                  : dragOver
                    ? "border-accent bg-accent/10"
                    : "border-slate-200 bg-paper-50/80 hover:border-accent/35 hover:bg-accent/[0.03]"
              }`}
            >
              <input
                type="file"
                accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
                className="sr-only"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                disabled={busy}
              />
              <p className="text-sm font-semibold text-ink-950">
                {file ? "Dosya seçildi" : "Dosya seçmek için tıklayın"}
              </p>
              <p className="text-xs text-ink-600 mt-1.5 font-medium">
                veya sürükleyip bırakın (tarayıcı desteğine bağlı)
              </p>
            </div>
          </label>
          {file && (
            <p className="mt-4 text-xs text-ink-600 font-medium truncate border-t border-slate-100 pt-4" title={file.name}>
              <span className="text-ink-500">Seçili:</span> {file.name}
            </p>
          )}
        </section>

        {/* Cevap anahtarı */}
        <section className="relative rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-card hover:shadow-card-hover transition-shadow duration-300">
          <div className="absolute top-6 right-6 sm:top-8 sm:right-8 flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-xs font-bold text-ink-500 tabular-nums">
            02
          </div>
          <div className="flex items-start gap-4 mb-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-500/10 text-violet-600">
              <IconDoc className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-ink-950 tracking-tight">Cevap anahtarı</h3>
              <p className="text-sm text-ink-600 mt-0.5 font-medium">Referans metin ve isteğe bağlı soru numaraları</p>
            </div>
          </div>
          <textarea
            className="w-full min-h-[200px] rounded-xl border border-slate-200 bg-paper-50/50 px-4 py-3 text-sm text-ink-950 placeholder:text-ink-600/50 font-medium leading-relaxed focus:outline-none focus:ring-2 focus:ring-accent/25 focus:border-accent transition-shadow resize-y"
            placeholder={`Örnek:\n1. Bitkiler güneş ışığını kullanarak fotosentez yapar.\n2. Mitokondri hücrede enerji üretir.`}
            value={answerKey}
            onChange={(e) => setAnswerKey(e.target.value)}
            disabled={busy}
          />
          <div className="mt-5 flex flex-wrap items-center gap-4">
            <label className="flex items-center gap-3 text-sm font-semibold text-ink-700">
              <span>Maks. puan</span>
              <input
                type="number"
                min={1}
                max={1000}
                className="w-28 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-bold text-ink-950 tabular-nums focus:outline-none focus:ring-2 focus:ring-accent/25 focus:border-accent"
                value={maxScore}
                onChange={(e) => setMaxScore(Number(e.target.value) || 100)}
                disabled={busy}
              />
            </label>
          </div>
        </section>
      </div>

      {/* Aksiyon */}
      <div className="mt-10 rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
          <div className="space-y-1">
            <p className="text-sm font-bold text-ink-950">03 — Değerlendirme</p>
            <p className="text-xs text-ink-600 font-medium max-w-md">
              Yükleme, OCR ve puanlama ardışık çalışır; işlem bitince sonuç sayfasına yönlendirilirsiniz.
            </p>
          </div>
          <button
            type="button"
            onClick={onGrade}
            disabled={busy}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-accent px-8 py-3.5 text-sm font-bold text-white shadow-glow hover:bg-accent-dim disabled:opacity-45 disabled:cursor-not-allowed disabled:shadow-none transition-all active:scale-[0.98]"
          >
            {busy ? (
              <>
                <span
                  className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin"
                  aria-hidden
                />
                İşleniyor…
              </>
            ) : (
              <>
                <IconSpark className="h-4 w-4 opacity-90" />
                Değerlendirmeyi başlat
              </>
            )}
          </button>
        </div>

        {busy && (
          <div className="mt-8 pt-6 border-t border-slate-100">
            <div className="flex gap-2 mb-3">
              {stepsBusy.map((label, i) => (
                <div
                  key={label}
                  className={`h-1 flex-1 rounded-full transition-colors ${
                    i < busyStep ? "bg-accent" : i === busyStep ? "bg-accent/50 animate-pulse" : "bg-slate-200"
                  }`}
                />
              ))}
            </div>
            <p className="text-xs font-semibold text-ink-600">{status || stepsBusy[busyStep] + "…"}</p>
          </div>
        )}

        {!busy && status && <p className="mt-6 text-sm font-medium text-ink-600 border-t border-slate-100 pt-6">{status}</p>}
      </div>

      {error && (
        <div
          className="mt-8 rounded-2xl border border-red-200/90 bg-red-50/90 px-5 py-4 text-sm text-red-900 font-medium leading-relaxed shadow-sm"
          role="alert"
        >
          {error}
        </div>
      )}

      {lastExtract && !busy && (
        <details className="mt-8 group rounded-2xl border border-slate-200/80 bg-white shadow-card overflow-hidden">
          <summary className="cursor-pointer list-none px-6 py-4 font-semibold text-ink-950 flex items-center justify-between gap-3 hover:bg-slate-50/80 transition-colors">
            <span>Son OCR çıktısı</span>
            <span className="text-ink-500 text-xs font-bold uppercase tracking-wide group-open:rotate-180 transition-transform">
              ▾
            </span>
          </summary>
          <pre className="px-6 pb-5 pt-0 text-xs leading-relaxed text-ink-700 whitespace-pre-wrap max-h-72 overflow-auto font-mono bg-paper-50/50 border-t border-slate-100">
            {lastExtract.extracted_text || "(boş)"}
          </pre>
        </details>
      )}
    </div>
  );
}
