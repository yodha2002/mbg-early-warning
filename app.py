"""
app.py — Dashboard Streamlit: Early Warning Keracunan MBG
Direktorat Cegah Tangkal — BPOM | Aktualisasi CPNS 2025

Sumber (10 media):
  Detik · Kompas · Tribun · Liputan6 · CNN Indonesia
  Merdeka · Kumparan · IDN Times · Suara · Okezone
  - KPI metrics (total berita, risiko merah, total korban)
  - Chart distribusi risiko & sumber berita
  - Tabel berita interaktif dengan filter
  - Alert otomatis untuk berita risiko merah
  - Statistik per provinsi
  - Trigger scraping manual (opsional)
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ─── Konfigurasi halaman ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Early Warning Keracunan MBG | BPOM",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Inject Supabase secrets dari Streamlit Cloud ─────────────────────────────
# Streamlit Cloud: tambahkan SUPABASE_URL & SUPABASE_KEY di Settings → Secrets
# Format secrets.toml:
#   SUPABASE_URL = "https://..."
#   SUPABASE_KEY = "eyJ..."
if "SUPABASE_URL" in st.secrets:
    os.environ["SUPABASE_URL"] = st.secrets["SUPABASE_URL"]
    os.environ["SUPABASE_KEY"] = st.secrets["SUPABASE_KEY"]

from database import get_all_articles


# ─── Load & cache data ────────────────────────────────────────────────────────
@st.cache_data(ttl=600)  # cache 10 menit, auto-refresh
def load_data() -> pd.DataFrame:
    articles = get_all_articles()
    if not articles:
        return pd.DataFrame()
    df = pd.DataFrame(articles)
    # Pastikan kolom numerik
    for col in ["score", "victim_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/BPOM_logo.svg/200px-BPOM_logo.svg.png",
        width=120,
    )
    st.title("Early Warning MBG")
    st.caption("Direktorat Cegah Tangkal — BPOM")
    st.divider()

    st.subheader("⚙️ Filter Data")
    risk_options = ["🔴 Merah", "🟡 Kuning", "🟢 Hijau"]
    selected_risks = st.multiselect(
        "Level Risiko", risk_options, default=["🔴 Merah", "🟡 Kuning"]
    )
    source_options = [
        "Detik", "Kompas", "Tribun", "Liputan6",
        "CNN Indonesia", "Merdeka", "Kumparan",
        "IDN Times", "Suara", "Okezone",
    ]
    selected_sources = st.multiselect("Sumber Berita", source_options, default=source_options)

    date_range = st.slider(
        "Rentang Hari Terakhir",
        min_value=1,
        max_value=30,
        value=7,
        step=1,
    )

    st.divider()
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("Sistem Early Warning Keracunan MBG\nAktualisasi CPNS 2025")


# ─── Main content ─────────────────────────────────────────────────────────────
st.title("⚠️ Sistem Early Warning Keracunan MBG")
st.caption(
    f"Pembaruan terakhir: {datetime.now().strftime('%d %B %Y, %H:%M')} WIB  |  "
    "Direktorat Cegah Tangkal — Badan Pengawas Obat dan Makanan"
)

df_raw = load_data()

if df_raw.empty:
    st.warning(
        "📭 Belum ada data di database.\n\n"
        "Jalankan pipeline pertama kali:\n```\npython scheduler.py\n```"
    )
    st.stop()

# ─── Filter ───────────────────────────────────────────────────────────────────
df = df_raw.copy()

# Filter sumber
if selected_sources:
    df = df[df["source"].isin(selected_sources)]

# Filter risiko
if selected_risks and "risk_level" in df.columns:
    df = df[df["risk_level"].isin(selected_risks)]

# Filter tanggal
if "created_at" in df.columns:
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    cutoff = datetime.now() - timedelta(days=date_range)
    df = df[df["created_at"] >= cutoff]


# ─── KPI Metrics ──────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("📰 Total Berita", len(df_raw))
with c2:
    n_merah = len(df_raw[df_raw.get("risk_level", pd.Series()).str.contains("Merah", na=False)])
    st.metric("🔴 Risiko Merah", n_merah, delta="Butuh tindak lanjut" if n_merah > 0 else "Aman")
with c3:
    n_kuning = len(df_raw[df_raw.get("risk_level", pd.Series()).str.contains("Kuning", na=False)])
    st.metric("🟡 Waspada", n_kuning)
with c4:
    total_korban = int(df_raw.get("victim_count", pd.Series(dtype=int)).sum())
    st.metric("👥 Total Korban Terdeteksi", total_korban)
with c5:
    skor_rata = int(df_raw.get("score", pd.Series(dtype=int)).mean()) if not df_raw.empty else 0
    st.metric("📊 Skor Rata-rata", skor_rata)


# ─── Alert Merah ──────────────────────────────────────────────────────────────
high_risk = df_raw[df_raw.get("risk_level", pd.Series()).str.contains("Merah", na=False)]
if not high_risk.empty:
    st.error(f"🚨 PERINGATAN: {len(high_risk)} berita dengan risiko tinggi terdeteksi!")
    with st.expander("Lihat berita risiko merah", expanded=True):
        for _, row in high_risk.head(5).iterrows():
            url = row.get("url", "#")
            title = row.get("title", "")
            score = row.get("score", 0)
            province = row.get("province", "")
            victims = row.get("victim_count", 0)
            st.markdown(
                f"**[{title}]({url})**  \n"
                f"Skor: `{score}` | Provinsi: `{province}` | Korban: `{victims}`"
            )
            st.divider()

st.divider()

# ─── Charts ───────────────────────────────────────────────────────────────────
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Distribusi Level Risiko")
    if "risk_level" in df_raw.columns and not df_raw.empty:
        risk_counts = df_raw["risk_level"].value_counts().reset_index()
        risk_counts.columns = ["Level Risiko", "Jumlah"]
        color_map = {"🔴 Merah": "#E24B4A", "🟡 Kuning": "#EF9F27", "🟢 Hijau": "#639922"}
        fig_pie = px.pie(
            risk_counts,
            values="Jumlah",
            names="Level Risiko",
            color="Level Risiko",
            color_discrete_map=color_map,
            hole=0.4,
        )
        fig_pie.update_layout(margin=dict(t=10, b=10), showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)

with col_chart2:
    st.subheader("Berita per Sumber")
    if "source" in df_raw.columns and not df_raw.empty:
        source_counts = df_raw["source"].value_counts().reset_index()
        source_counts.columns = ["Sumber", "Jumlah"]
        fig_bar = px.bar(
            source_counts,
            x="Sumber",
            y="Jumlah",
            color="Sumber",
            color_discrete_sequence=[
                "#185FA5", "#0F6E56", "#993C1D", "#3B6D11", "#534AB7",
                "#854F0B", "#993556", "#5F5E5A", "#0F6E56", "#A32D2D",
            ],
            text="Jumlah",
        )
        fig_bar.update_layout(
            showlegend=False,
            margin=dict(t=10, b=10),
            xaxis_title="",
            yaxis_title="Jumlah Artikel",
        )
        fig_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_bar, use_container_width=True)


# ─── Tren waktu ───────────────────────────────────────────────────────────────
if "created_at" in df_raw.columns and not df_raw.empty:
    st.subheader("Tren Berita Harian")
    df_trend = df_raw.copy()
    df_trend["created_at"] = pd.to_datetime(df_trend["created_at"], errors="coerce")
    df_trend["tanggal"] = df_trend["created_at"].dt.date
    trend = df_trend.groupby("tanggal").size().reset_index(name="jumlah")
    fig_line = px.line(
        trend,
        x="tanggal",
        y="jumlah",
        markers=True,
        labels={"tanggal": "Tanggal", "jumlah": "Jumlah Berita"},
    )
    fig_line.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig_line, use_container_width=True)


# ─── Peta sebaran provinsi ────────────────────────────────────────────────────
if "province" in df_raw.columns:
    prov_df = df_raw[
        (df_raw["province"].notna()) &
        (df_raw["province"] != "Tidak Terdeteksi") &
        (df_raw["province"] != "")
    ]
    if not prov_df.empty:
        st.subheader("📍 Sebaran Laporan per Provinsi")
        prov_counts = prov_df["province"].value_counts().reset_index()
        prov_counts.columns = ["Provinsi", "Jumlah Laporan"]
        fig_prov = px.bar(
            prov_counts,
            x="Jumlah Laporan",
            y="Provinsi",
            orientation="h",
            color="Jumlah Laporan",
            color_continuous_scale=["#FCDE5A", "#E85D24", "#A32D2D"],
        )
        fig_prov.update_layout(
            margin=dict(t=10, b=10),
            yaxis=dict(categoryorder="total ascending"),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_prov, use_container_width=True)


# ─── Tabel berita ─────────────────────────────────────────────────────────────
st.subheader("📋 Daftar Berita Terfilter")
st.caption(f"Menampilkan {len(df)} dari {len(df_raw)} total berita")

if not df.empty:
    display_cols = {
        "source": "Sumber",
        "title": "Judul Berita",
        "published_date": "Tanggal",
        "score": "Skor",
        "risk_level": "Level Risiko",
        "province": "Provinsi",
        "victim_count": "Korban",
        "url": "URL",
    }
    available = {k: v for k, v in display_cols.items() if k in df.columns}
    df_display = df[list(available.keys())].rename(columns=available)

    # Tampilkan sebagai tabel interaktif
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "URL": st.column_config.LinkColumn("URL", display_text="🔗 Buka"),
            "Skor": st.column_config.NumberColumn("Skor", format="%d"),
            "Korban": st.column_config.NumberColumn("Korban", format="%d orang"),
        },
    )

    # Download CSV
    csv = df_display.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Download sebagai CSV",
        data=csv,
        file_name=f"mbg_early_warning_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
else:
    st.info("Tidak ada data sesuai filter yang dipilih.")

# ─── Footer ───────────────────────────────────────────────────────────────────
st.divider()
col_f1, col_f2 = st.columns(2)
with col_f1:
    st.caption("🏛️ **Direktorat Cegah Tangkal — BPOM RI**")
    st.caption("Sistem Early Warning Keracunan Makan Bergizi Gratis (MBG)")
with col_f2:
    st.caption("⚙️ Aktualisasi CPNS 2025")
    st.caption(f"Versi sistem: 1.1.0 | 10 sumber media | Data diperbarui setiap 6 jam via GitHub Actions")
