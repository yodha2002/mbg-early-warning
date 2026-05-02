@echo off
echo ============================================
echo  Setup: Early Warning Keracunan MBG - BPOM
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python tidak ditemukan!
    echo Download di https://python.org pilih versi 3.11+
    pause
    exit /b 1
)
echo [OK] Python ditemukan.

echo.
echo [1/4] Membuat virtual environment...
if exist venv (
    echo venv sudah ada, skip.
) else (
    python -m venv venv
    echo venv berhasil dibuat.
)

echo.
echo [2/4] Mengaktifkan virtual environment...
call venv\Scripts\activate.bat
echo Aktif.

echo.
echo [3/4] Menginstall dependensi...
pip install --upgrade pip --quiet
pip install -r requirements.txt
echo Selesai install.

echo.
echo [4/4] Membuat file .env...
if not exist .env (
    copy .env.example .env >nul
    echo File .env dibuat.
    echo.
    echo =============================================
    echo  Buka file .env dan isi dengan:
    echo  SUPABASE_URL dan SUPABASE_KEY kamu
    echo =============================================
    echo.
    notepad .env
    pause
) else (
    echo File .env sudah ada.
)

echo.
echo Menjalankan scraping pertama...
python scheduler.py

echo.
echo ============================================
echo  SELESAI! Jalankan dashboard dengan:
echo  streamlit run app.py
echo ============================================
pause
