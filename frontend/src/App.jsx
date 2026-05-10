import { Routes, Route, Link, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import Results from "./pages/Results.jsx";

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/75 backdrop-blur-xl supports-[backdrop-filter]:bg-white/65">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-6">
          <Link to="/" className="flex items-center gap-3 min-w-0 group">
            <span className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-indigo-600 text-white font-bold text-sm shadow-glow ring-4 ring-white/80">
              EY
              <span className="absolute inset-0 rounded-xl ring-1 ring-inset ring-white/20" aria-hidden />
            </span>
            <div className="min-w-0">
              <p className="text-[15px] font-semibold text-ink-950 leading-tight tracking-tight group-hover:text-accent transition-colors truncate">
                El Yazısı Sınav Okuyucu
              </p>
              <p className="text-[11px] text-ink-600 font-medium truncate">
                OCR · Anlamsal &amp; kelime benzerliği · Yerel
              </p>
            </div>
          </Link>
          <nav className="flex items-center gap-1">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  isActive
                    ? "bg-accent/10 text-accent shadow-sm"
                    : "text-ink-700 hover:text-ink-950 hover:bg-slate-100/80"
                }`
              }
              end
            >
              Panel
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/sonuc/:gradeId" element={<Results />} />
          <Route
            path="*"
            element={
              <div className="max-w-lg mx-auto px-4 py-24 text-center space-y-5 animate-fade-in">
                <p className="text-ink-950 font-semibold text-lg">Sayfa bulunamadı</p>
                <Link
                  to="/"
                  className="inline-flex items-center justify-center rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-white shadow-glow hover:bg-accent-dim transition-colors"
                >
                  Panele dön
                </Link>
              </div>
            }
          />
        </Routes>
      </main>

      <footer className="border-t border-slate-200/80 bg-white/60 backdrop-blur-sm mt-auto">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-ink-600 font-medium">
          <span>Çoklu OCR · MiniLM / TF‑IDF benzerlik</span>
          <span className="text-ink-500">Yerel prototip — veri sunucuya gönderilmez</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
