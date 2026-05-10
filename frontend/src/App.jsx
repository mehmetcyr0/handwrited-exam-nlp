import { Routes, Route, Link, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import Results from "./pages/Results.jsx";

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/70 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2 group">
            <span className="h-9 w-9 rounded-xl bg-gradient-to-br from-accent to-indigo-600 shadow-md shadow-accent/25 flex items-center justify-center text-white font-bold text-sm">
              EY
            </span>
            <div>
              <h1 className="text-lg font-semibold text-ink-950 leading-tight group-hover:text-accent transition-colors">
                El Yazısı Sınav Okuyucu
              </h1>
              <p className="text-xs text-ink-700">Anlamsal puanlama · OCR · Yerel çalışır</p>
            </div>
          </Link>
          <nav className="flex gap-1 text-sm">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `px-3 py-2 rounded-lg font-medium transition-colors ${
                  isActive ? "bg-paper-100 text-accent" : "text-ink-700 hover:bg-paper-50"
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
              <div className="max-w-lg mx-auto px-4 py-20 text-center space-y-4">
                <p className="text-ink-950 font-medium">Sayfa bulunamadı.</p>
                <Link to="/" className="text-accent font-medium hover:underline">
                  Panele dön
                </Link>
              </div>
            }
          />
        </Routes>
      </main>

      <footer className="border-t border-slate-200/80 bg-white py-6 text-center text-xs text-ink-700">
        Prototip — PaddleOCR + sentence-transformers (all-MiniLM-L6-v2)
      </footer>
    </div>
  );
}

export default App;
