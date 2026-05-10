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
      <div className="max-w-3xl mx-auto px-4 py-16">
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-800">
          {error}
        </div>
        <Link to="/" className="inline-block mt-6 text-accent font-medium hover:underline">
          Panele dön
        </Link>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center text-ink-700">
        Sonuçlar yükleniyor…
      </div>
    );
  }

  const sim = data.similarity_percent;
  const pctColor =
    sim >= 90 ? "text-emerald-600" : sim >= 70 ? "text-blue-600" : sim >= 50 ? "text-amber-600" : "text-red-600";

  return (
    <div className="max-w-3xl mx-auto px-4 py-10 space-y-8">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-semibold text-ink-950">Değerlendirme sonucu</h2>
          <p className="text-sm text-ink-700 mt-1">Kayıt #{data.grade_id}</p>
        </div>
        <Link
          to="/"
          className="text-sm font-medium text-accent hover:underline shrink-0"
        >
          Yeni sınav
        </Link>
      </div>

      <div className="grid sm:grid-cols-3 gap-4">
        <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-ink-700 font-medium">Anlamsal benzerlik</p>
          <p className={`text-3xl font-bold mt-1 ${pctColor}`}>%{Number(sim).toFixed(1)}</p>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-ink-700 font-medium">Puan</p>
          <p className="text-3xl font-bold mt-1 text-ink-950">
            {Number(data.final_score).toFixed(1)}
            <span className="text-lg text-ink-700 font-normal">
              {" "}
              / {Number(data.max_score).toFixed(0)}
            </span>
          </p>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm sm:col-span-1">
          <p className="text-xs uppercase tracking-wide text-ink-700 font-medium">Tarih</p>
          <p className="text-sm font-medium mt-2 text-ink-950">{data.created_at || "—"}</p>
        </div>
      </div>

      <section className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm space-y-3">
        <h3 className="font-semibold text-ink-950">Geri bildirim</h3>
        <p className="text-ink-700 leading-relaxed">{data.feedback}</p>
      </section>

      <section className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm space-y-3">
        <h3 className="font-semibold text-ink-950">Çıkarılan metin (öğrenci)</h3>
        <pre className="text-sm text-ink-700 whitespace-pre-wrap bg-paper-50 rounded-xl p-4 max-h-80 overflow-auto border border-slate-100">
          {data.extracted_text || "(boş)"}
        </pre>
      </section>

      <section className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm space-y-3">
        <h3 className="font-semibold text-ink-950">Cevap anahtarı (kullanılan)</h3>
        <pre className="text-sm text-ink-700 whitespace-pre-wrap bg-paper-50 rounded-xl p-4 max-h-64 overflow-auto border border-slate-100">
          {data.answer_key}
        </pre>
      </section>
    </div>
  );
}
