# El Yazısı Sınav Okuyucu

Yerelde çalışan, el yazısı sınav görsellerini (JPG/PNG/PDF) yükleyip **OpenCV** ile ön işleme, **PaddleOCR** ile metin çıkarma ve **sentence-transformers** (`all-MiniLM-L6-v2`) ile **anlamsal benzerlik** üzerinden puanlama yapan web uygulaması.

## Mimari

- **Backend:** FastAPI, SQLite, modüler `services/` katmanı  
- **Frontend:** React (Vite), Tailwind CSS  
- **API:** `POST /api/upload`, `POST /api/extract`, `POST /api/grade`, `GET /api/results/{id}`

## İkisini birden çalıştırma (önerilen)

Proje klasöründeki **`run-all.cmd`** dosyasına çift tıklayın (veya Explorer adres çubuğuna `run-all.cmd` yazıp Enter).

- İlk seferde `pip install` ve gerekirse `npm install` çalışır (biraz sürebilir).
- Ardından iki ayrı pencere açılır: **API** (port 8000) ve **Arayüz** (port 5173).

**Tarayıcıda açın:** [http://localhost:5173](http://localhost:5173) — bu adres uygulama arayüzüdür.  
`http://localhost:8000` yalnızca API sunucusudur (Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)). Eski davranışta kök URL “Not Found” veriyordu; artık kısa bir JSON bilgisi döner.

Alternatif: `start-dev.ps1` (PowerShell) aynı işi yapar; gerekirse sağ tık → **PowerShell ile çalıştır**.  
Yalnızca API: **`backend\start-api.cmd`** (çift tık; `uvicorn` PATH gerekmez).

---

## Kurulum (manuel, ayrı terminaller)

### 1. Python sanal ortamı

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

İlk çalıştırmada `sentence-transformers` modelini ve PaddleOCR ağırlıklarını indirir; internet gerekir.

**pip / METADATA / bozuk `.venv` uyarıları:** Tüm Python pencerelerini kapatıp **`backend\reset-venv.cmd`** çalıştırın; ardından `run-all.cmd` veya `start-api.cmd` ile devam edin.

### 2. Backend’i başlatma

Windows’ta **`backend\start-api.cmd`** dosyasına çift tıklayabilirsiniz (venv yoksa oluşturur, API’yi başlatır).

PowerShell’de (`uvicorn` komutu genelde tanınmaz; **`python -m uvicorn`** kullanın):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Aktive etmeden:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Tarayıcı: [http://localhost:5173](http://localhost:5173) — Vite, API isteklerini geliştirme modunda `8000` portuna yönlendirir.

## Kullanım

1. Panelde sınav dosyasını yükleyin.  
2. Cevap anahtarını metin olarak yazın (numaralı satırlar, örn. `1. ...`, `2. ...`, mümkün olduğunca öğrenci çıktısıyla aynı soru sayısı).  
3. **Değerlendirmeyi başlat** — OCR sonrası anlamsal skor ve puan sonuç sayfasında gösterilir.

## Proje yapısı

```
yazılı sınav/
├── backend/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   │   ├── image_processing.py
│   │   ├── ocr_service.py
│   │   ├── semantic_service.py
│   │   └── grading_service.py
│   ├── uploads/
│   └── database/
├── frontend/
└── README.md
```

## Notlar

- PDF için şu an **yalnızca ilk sayfa** işlenir (OCR hattına dönüştürülür).  
- Türkçe el yazısı için PaddleOCR dil/model ayarları `services/ocr_service.py` içinde geliştirilebilir (bonus: Türkçe optimizasyon).  
- Tamamen yerel çalışır; harici bulut API’si kullanılmaz.
