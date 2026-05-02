# ⚠️ Early Warning Keracunan MBG — BPOM

**Sistem pemantauan berita keracunan Program Makan Bergizi Gratis (MBG)**  
Direktorat Cegah Tangkal — Badan Pengawas Obat dan Makanan  
*Aktualisasi CPNS 2025*

---

## 🏗️ Arsitektur Sistem

```
[Detik.com] [Kompas.com] [Tribunnews] [Liputan6] [CNN Indonesia]
[Merdeka]   [Kumparan]   [IDN Times]  [Suara]    [Okezone]
      ↓             ↓           ↓           ↓           ↓
              scraper.py (BeautifulSoup — 10 sumber)
                       ↓
        database.py (Supabase / SQLite)
                  ↓
           analyzer.py (Keyword Scoring)
                  ↓
        app.py (Streamlit Dashboard)

Penjadwalan otomatis: GitHub Actions (cron 6 jam)
```

## 📁 Struktur File

```
mbg_early_warning/
├── scraper.py              # Scraping Detik, Kompas, Tribun
├── database.py             # Handler DB (Supabase + SQLite fallback)
├── analyzer.py             # Scoring & klasifikasi risiko
├── scheduler.py            # Orchestrator pipeline
├── app.py                  # Dashboard Streamlit
├── requirements.txt        # Dependensi Python
├── .env.example            # Template konfigurasi
├── .gitignore
├── setup.bat               # Setup otomatis Windows
└── .github/
    └── workflows/
        └── scrape.yml      # GitHub Actions workflow
```

---

## 🚀 Cara Setup (Windows)

### Step 1 — Clone repository

```cmd
git clone https://github.com/USERNAME/mbg-early-warning.git
cd mbg-early-warning
```

### Step 2 — Setup otomatis

Klik dua kali `setup.bat` atau jalankan:

```cmd
setup.bat
```

Script ini akan otomatis:
1. Membuat virtual environment
2. Install semua dependensi
3. Membuat file `.env`
4. Menjalankan scraping pertama kali

### Step 3 — Isi konfigurasi Supabase

Buka file `.env` dan isi:

```env
SUPABASE_URL=https://xxxxxx.supabase.co
SUPABASE_KEY=eyJhbGci...
```

> **Cara buat Supabase gratis:**
> 1. Daftar di [supabase.com](https://supabase.com)
> 2. Buat project baru
> 3. Masuk ke `Project Settings → API`
> 4. Salin **Project URL** dan **anon public** key

### Step 4 — Buat tabel di Supabase

Di Supabase, buka **SQL Editor** dan jalankan:

```sql
CREATE TABLE articles (
  id            BIGSERIAL PRIMARY KEY,
  source        TEXT NOT NULL,
  title         TEXT UNIQUE NOT NULL,
  url           TEXT,
  published_date TEXT,
  content       TEXT,
  score         INTEGER DEFAULT 0,
  risk_level    TEXT DEFAULT 'Hijau',
  province      TEXT DEFAULT '',
  victim_count  INTEGER DEFAULT 0,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

### Step 5 — Jalankan dashboard

```cmd
call venv\Scripts\activate
streamlit run app.py
```

Dashboard terbuka di `http://localhost:8501`

---

## ☁️ Deployment ke Streamlit Cloud

### 1. Push ke GitHub

```cmd
git add .
git commit -m "Initial commit: MBG Early Warning System"
git push origin main
```

### 2. Deploy di Streamlit Cloud

1. Buka [share.streamlit.io](https://share.streamlit.io)
2. Klik **New app**
3. Pilih repository `mbg-early-warning`
4. Main file path: `app.py`
5. Klik **Deploy**

### 3. Tambahkan secrets di Streamlit Cloud

Di Streamlit Cloud → App Settings → **Secrets**:

```toml
SUPABASE_URL = "https://xxxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGci..."
```

### 4. Aktifkan GitHub Actions

1. Di GitHub repository → **Settings → Secrets and variables → Actions**
2. Tambahkan:
   - `SUPABASE_URL` = URL Supabase
   - `SUPABASE_KEY` = API key Supabase
3. GitHub Actions akan scraping otomatis setiap 6 jam

---

## 🖥️ Rekomendasi Server

| Kebutuhan | Rekomendasi | Biaya |
|-----------|-------------|-------|
| Dashboard | Streamlit Cloud | **Gratis** |
| Database | Supabase (500 MB) | **Gratis** |
| Scheduler | GitHub Actions (2.000 mnt/bln) | **Gratis** |
| Monitoring | Streamlit built-in logs | **Gratis** |

> Untuk produksi penuh di server BPOM:
> - **VPS**: Contabo 4GB RAM (~$5/bln) atau Google Cloud E2-medium
> - **Database**: PostgreSQL on-premise atau Cloud SQL
> - **Scheduler**: Systemd timer atau Crontab Linux

---

## 📊 Sistem Scoring Risiko

| Level | Skor | Arti |
|-------|------|------|
| 🟢 Hijau | 0–29 | Informasi umum, belum ada indikasi insiden |
| 🟡 Kuning | 30–59 | Potensi insiden, perlu pemantauan aktif |
| 🔴 Merah | 60–100 | Insiden terkonfirmasi, tindak lanjut segera |

**Faktor yang meningkatkan skor:**
- Kata kunci keracunan, UGD, kritis, meninggal
- Jumlah korban (siswa/murid)
- Gejala klinis (muntah, diare, kejang)
- Konteks program MBG

---

## 🔧 Perintah Berguna

```cmd
# Aktifkan venv dulu
call venv\Scripts\activate

# Jalankan scraping sekali
python scheduler.py

# Jalankan scraping terus-menerus (interval 6 jam)
python scheduler.py --loop --interval 6

# Test scraper saja
python scraper.py

# Test analyzer saja
python analyzer.py

# Test database saja
python database.py

# Jalankan dashboard
streamlit run app.py
```

---

## ⚠️ Catatan Penting

1. **Selector HTML bisa berubah** — Jika berita tidak muncul, periksa dan update selector di `scraper.py`
2. **Rate limiting** — Jangan hapus `DELAY_SECONDS` di scraper.py untuk menghindari pemblokiran
3. **Data sensitif** — Jangan pernah commit file `.env` ke GitHub (sudah ada di `.gitignore`)
4. **Free tier Supabase** — Batas 500 MB storage dan 2 juta rows/bulan, cukup untuk sistem ini

---

*Dibuat dalam rangka Aktualisasi CPNS 2025 — Direktorat Cegah Tangkal BPOM RI*
