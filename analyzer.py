"""
analyzer.py — Sistem Analisis & Scoring Risiko Keracunan MBG
Metode: Keyword-based scoring dengan bobot berbasis domain BPOM/kesehatan publik.

Level risiko:
  🟢 Hijau  : skor 0–29   (informasi umum, belum ada indikasi insiden)
  🟡 Kuning : skor 30–59  (potensi insiden, perlu pemantauan)
  🔴 Merah  : skor 60–100 (insiden terkonfirmasi, perlu tindak lanjut segera)
"""

import re
import logging
from database import get_all_articles, update_article_score

logger = logging.getLogger(__name__)

# ─── Kamus bobot kata kunci ───────────────────────────────────────────────────
# Sesuaikan bobot berdasarkan prioritas BPOM Direktorat Cegah Tangkal

KEYWORD_WEIGHTS: dict[str, int] = {
    # Insiden serius (bobot tinggi)
    "meninggal":            35,
    "tewas":                35,
    "kritis":               30,
    "masuk icu":            30,
    "dirawat intensif":     28,
    "keracunan massal":     28,
    "keracunan parah":      25,
    "keracunan":            22,
    "masuk rumah sakit":    20,
    "dibawa ke ugd":        20,
    "ugd":                  18,
    "dirawat":              15,
    "korban":               15,
    "puskesmas":            12,

    # Gejala relevan (bobot menengah)
    "mual muntah":          14,
    "muntah darah":         20,
    "diare parah":          18,
    "diare":                12,
    "kejang":               20,
    "tidak sadarkan diri":  25,
    "pingsan":              18,
    "pusing":               10,
    "sakit perut":          10,
    "mual":                 8,

    # Konteks MBG (bobot dasar)
    "makan bergizi gratis": 12,
    "mbg":                  12,
    "makan siang gratis":   12,
    "program makan":        8,
    "catering sekolah":     10,
    "makanan sekolah":      8,

    # Subyek rentan (bobot dasar)
    "siswa":                6,
    "murid":                6,
    "pelajar":              6,
    "anak sekolah":         8,
    "sd":                   5,
    "smp":                  5,
    "sma":                  5,
    "santri":               5,

    # Penyelidikan/respons (menambah konteks)
    "bpom":                 10,
    "dinas kesehatan":      8,
    "diselidiki":           5,
    "diduga":               5,
    "dilaporkan":           4,
}

# ─── Daftar provinsi untuk ekstraksi lokasi ───────────────────────────────────
PROVINCES = [
    "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Kepulauan Riau",
    "Jambi", "Bengkulu", "Sumatera Selatan", "Bangka Belitung", "Lampung",
    "Banten", "DKI Jakarta", "Jakarta", "Jawa Barat", "Jawa Tengah",
    "DI Yogyakarta", "Yogyakarta", "Jawa Timur", "Bali",
    "Nusa Tenggara Barat", "NTB", "Nusa Tenggara Timur", "NTT",
    "Kalimantan Barat", "Kalimantan Tengah", "Kalimantan Selatan",
    "Kalimantan Timur", "Kalimantan Utara", "Sulawesi Utara",
    "Sulawesi Tengah", "Sulawesi Selatan", "Sulawesi Tenggara",
    "Gorontalo", "Sulawesi Barat", "Maluku", "Maluku Utara",
    "Papua", "Papua Barat", "Papua Selatan", "Papua Tengah",
]

# ─── Fungsi analisis ──────────────────────────────────────────────────────────
def calculate_score(title: str, content: str = "") -> int:
    """
    Hitung skor risiko (0–100) dari teks berita.
    Semakin tinggi skor = semakin serius indikasi keracunan.
    """
    text = (title + " " + content).lower()
    score = 0

    for keyword, weight in KEYWORD_WEIGHTS.items():
        if keyword.lower() in text:
            score += weight

    # Bonus skor berdasarkan jumlah korban
    victim_count = extract_victim_count(title + " " + content)
    if victim_count > 0:
        # +1 poin per 2 korban, maksimal +20
        score += min(victim_count // 2, 20)

    return min(score, 100)


def get_risk_level(score: int) -> str:
    """Klasifikasikan skor menjadi level risiko."""
    if score >= 60:
        return "🔴 Merah"
    elif score >= 30:
        return "🟡 Kuning"
    else:
        return "🟢 Hijau"


def extract_victim_count(text: str) -> int:
    """
    Ekstrak jumlah korban/penderita dari teks.
    Contoh: '25 siswa dirawat', 'sebanyak 40 orang', '10 anak'
    """
    patterns = [
        r"(\d+)\s*(?:siswa|murid|pelajar|orang|warga|korban|anak|santri)",
        r"sebanyak\s*(\d+)",
        r"(\d+)\s*(?:dari|orang)\s*(?:dirawat|keracunan|sakit)",
        r"lebih\s*dari\s*(\d+)",
    ]
    max_count = 0
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            try:
                val = int(m)
                if val > max_count:
                    max_count = val
            except ValueError:
                pass
    return max_count


def extract_province(text: str) -> str:
    """Deteksi nama provinsi dari teks berita."""
    for prov in PROVINCES:
        if prov.lower() in text.lower():
            return prov
    return "Tidak Terdeteksi"


# ─── Proses semua artikel di database ────────────────────────────────────────
def analyze_all():
    """
    Baca semua artikel dari DB, hitung skor & metadata, lalu update.
    """
    articles = get_all_articles()
    if not articles:
        logger.warning("Tidak ada artikel di database untuk dianalisis.")
        return

    counters = {"hijau": 0, "kuning": 0, "merah": 0}

    for a in articles:
        title = a.get("title", "")
        content = a.get("content", "")
        full_text = title + " " + content

        score = calculate_score(title, content)
        risk_level = get_risk_level(score)
        province = extract_province(full_text)
        victim_count = extract_victim_count(full_text)

        update_article_score(
            article_id=a["id"],
            score=score,
            risk_level=risk_level,
            province=province,
            victim_count=victim_count,
        )

        level_key = risk_level.split()[-1].lower()
        if level_key in counters:
            counters[level_key] += 1

    logger.info(
        f"Analisis selesai: {len(articles)} artikel | "
        f"🟢 Hijau: {counters['hijau']} | "
        f"🟡 Kuning: {counters['kuning']} | "
        f"🔴 Merah: {counters['merah']}"
    )


# ─── Test mandiri ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Contoh pengujian scoring
    test_cases = [
        ("25 siswa SD keracunan makan bergizi gratis, dibawa ke UGD Puskesmas", ""),
        ("Kemenkes tinjau program MBG di Jawa Barat", ""),
        ("Menu makan siang sekolah diganti setelah 3 murid mual muntah diare", ""),
        ("Program makan bergizi gratis diluncurkan di 10 kota", ""),
        ("40 pelajar SMP keracunan massal, 2 kritis dirawat intensif Sumatera Utara", ""),
    ]

    print("=" * 65)
    print(f"{'Judul':<45} {'Skor':>5}  Level")
    print("=" * 65)
    for title, content in test_cases:
        score = calculate_score(title, content)
        level = get_risk_level(score)
        victims = extract_victim_count(title)
        province = extract_province(title)
        print(f"{title[:45]:<45} {score:>5}  {level}")
        print(f"  → Korban: {victims}, Provinsi: {province}")
    print("=" * 65)
