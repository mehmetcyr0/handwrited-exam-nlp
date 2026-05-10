import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getResults } from "../api.js";

export default function Results() {
  const { gradeId } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await getResults(Number(gradeId));
        if (!cancelled) setData(r);
      } catch (e) {
        if (!cancelled) setError(e.message || String(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [gradeId]);

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-20 animate-fade-in">
        <div className="rounded-2xl border border-red-200/90 bg-red-50/90 px-5 py-4 text-sm font-medium text-red-900 shadow-card">
          {error}
        </div>
        <Link
          to="/"
          className="inline-flex mt-8 rounded-xl bg-accent px-5 py-2.5 text-sm font-bold text-white shadow-glow hover:bg-accent-dim transition-colors"
        >
          Panele dön
        </Link>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-24 flex flex-col items-center justify-center gap-4 text-ink-600 animate-fade-in">
        <span className="h-8 w-8 rounded-full border-2 border-accent/20 border-t-accent animate-spin" />
        <p className="text-sm font-semibold">Sonuçlar yükleniyor…</p>
      </div>
    );
  }

  const sim = data.similarity_percent;
  const pctColor =
    sim >= 80 ? "text-emerald-600" : sim >= 60 ? "text-blue-600" : sim >= 40 ? "text-amber-600" : "text-red-600";

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-14 space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-ink-500 mb-1">Sonuç</p>
          <h2 className="text-3xl font-bold text-ink-950 tracking-tight">Değerlendirme özeti</h2>
          <p className="text-sm text-ink-600 font-medium mt-1.5">Kayıt #{data.grade_id}</p>
        </div>
        <Link
          to="/"
          className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-bold text-ink-800 shadow-sm hover:border-accent/40 hover:text-accent transition-colors shrink-0"
        >
          Yeni sınav
        </Link>
      </div>

      <div className="grid sm:grid-cols-3 gap-4 lg:gap-6">
        <div className="rounded-2xl bg-white border border-slate-200/80 p-6 shadow-card">
          <p className="text-[11px] font-bold uppercase tracking-wider text-ink-500">Birleşik benzerlik</p>
          <p className={`text-4xl font-bold mt-2 tabular-nums tracking-tight ${pctColor}`}>%{Number(sim).toFixed(1)}</p>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200/80 p-6 shadow-card">
          <p className="text-[11px] font-bold uppercase tracking-wider text-ink-500">Puan</p>
          <p className="text-4xl font-bold mt-2 text-ink-950 tabular-nums tracking-tight">
            {Number(data.final_score).toFixed(1)}
            <span className="text-xl text-ink-600 font-semibold">
              {" "}
              / {Number(data.max_score).toFixed(0)}
            </span>
          </p>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200/80 p-6 shadow-card">
          <p className="text-[11px] font-bold uppercase tracking-wider text-ink-500">Tarih</p>
          <p className="text-sm font-semibold mt-3 text-ink-950">{data.created_at || "—"}</p>
        </div>
      </div>

      <section className="rounded-2xl bg-white border border-slate-200/80 p-6 sm:p-8 shadow-card space-y-3">
        <h3 className="text-base font-bold text-ink-950">Geri bildirim</h3>
        <p className="text-ink-700 leading-relaxed text-[15px] font-medium">{data.feedback}</p>
      </section>

      <section className="rounded-2xl bg-white border border-slate-200/80 p-6 sm:p-8 shadow-card space-y-3">
        <h3 className="text-base font-bold text-ink-950">Çıkarılan metin (öğrenci)</h3>
        <pre className="text-sm text-ink-700 whitespace-pre-wrap bg-paper-50/80 rounded-xl p-4 max-h-80 overflow-auto border border-slate-100 font-mono leading-relaxed">
          {data.extracted_text || "(boş)"}
        </pre>
      </section>

      <section className="rounded-2xl bg-white border border-slate-200/80 p-6 sm:p-8 shadow-card space-y-3">
        <h3 className="text-base font-bold text-ink-950">Cevap anahtarı (kullanılan)</h3>
        <pre className="text-sm text-ink-700 whitespace-pre-wrap bg-paper-50/80 rounded-xl p-4 max-h-64 overflow-auto border border-slate-100 font-mono leading-relaxed">
          {data.answer_key}
        </pre>
      </section>
    </div>
  );
}
