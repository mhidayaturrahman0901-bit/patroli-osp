import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from PIL import Image, UnidentifiedImageError, ImageFilter
import imagehash
import io
import os
import sqlite3
import hashlib
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

# =========================
# CONFIG UI
# =========================
st.set_page_config(page_title="Audit Foto Patroli - Center Focused", layout="wide")
st.title("🕵️ AUDIT FOTO PATROLI")
st.markdown("### Mode: **Center-Only Audit** (Abaikan Logo & Teks GEO)")

# =========================
# DATABASE PATH SETUP
# =========================
DB_PATH = "audit_history.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            sha256 TEXT PRIMARY KEY,
            phash  TEXT,
            source_file TEXT,
            sheet TEXT,
            location TEXT,
            cluster TEXT,
            segment TEXT,
            first_seen DATE
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_phash ON history(phash)")
    return conn

def db_lookup(conn, sha256_hex, phash_str):
    exact = conn.execute("SELECT * FROM history WHERE sha256=?", (sha256_hex,)).fetchone()
    ph = conn.execute("SELECT * FROM history WHERE phash=? LIMIT 1", (phash_str,)).fetchone()
    return exact, ph

# =========================
# LOGIKA POTONG TENGAH (CROP) & HASH
# =========================
def compute_hashes_from_bytes(img_bytes):
    try:
        img_original = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        w, h = img_original.size
        
        # POTONG TENGAH: Buang 25% Atas (Logo) & 25% Bawah (GEO)
        top = int(h * 0.25)
        bottom = int(h * 0.75)
        left = int(w * 0.10)
        right = int(w * 0.90)
        
        audit_area = img_original.crop((left, top, right, bottom))

        # Hitung sidik jari dari area tengah saja
        thumb = audit_area.copy()
        thumb.thumbnail((260, 260))
        ph = str(imagehash.phash(thumb))
        
        # SHA256 dari area tengah
        img_byte_arr = io.BytesIO()
        audit_area.save(img_byte_arr, format='PNG')
        sh = hashlib.sha256(img_byte_arr.getvalue()).hexdigest()
        
        return sh, ph, thumb, img_original
    except:
        return None, None, None, None

# =========================
# FUNGSI PEMBANTU EXCEL
# =========================
def find_cols(ws):
    # Cari posisi kolom Cluster, Segment, dan Link secara otomatis
    col_c, col_s, col_l = 2, 3, 7 # Default B, C, G
    for r in range(1, 10):
        for c in range(1, 15):
            v = str(ws.cell(r, c).value).lower() if ws.cell(r, c).value else ""
            if "cluster" in v: col_c = c
            if "segment" in v: col_s = c
            if "link" in v or "url" in v: col_l = c
    return col_c, col_s, col_l

# =========================
# PROSES UTAMA
# =========================
uploaded = st.file_uploader("Upload Excel Patroli (.xlsx)", type=["xlsx"])

if uploaded:
    # Simpan file sementara
    tmp_path = "temp_upload.xlsx"
    with open(tmp_path, "wb") as f:
        f.write(uploaded.getbuffer())
    
    st.success("✅ File terbaca. Klik tombol di bawah untuk mulai audit.")
    
    if st.button("🚀 MULAI AUDIT SEKARANG"):
        conn = get_db()
        wb = load_workbook(tmp_path, data_only=True)
        all_data = []
        
        with st.status("Sedang mengaudit foto (Hanya area tengah)...") as status:
            for ws in wb.worksheets:
                col_c, col_s, col_l = find_cols(ws)
                
                # 1. Ambil Foto yang nempel di Excel (Embedded)
                imgs = getattr(ws, "_images", [])
                for img_obj in imgs:
                    try:
                        row = img_obj.anchor._from.row + 1
                        raw = img_obj._data()
                        sh, ph, thumb, full = compute_hashes_from_bytes(raw)
                        
                        if sh:
                            # Cek Database
                            exact, sim = db_lookup(conn, sh, ph)
                            
                            status_akhir = "✅ VALID"
                            detail = "Foto Baru"
                            
                            if exact: 
                                status_akhir = "❌ GUGUR"
                                detail = f"Sama persis dengan file lama ({exact[2]})"
                            elif sim:
                                status_akhir = "⚠️ CEK MANUAL"
                                detail = f"Mirip foto lama ({sim[2]})"
                            
                            # Simpan ke DB jika Valid
                            if status_akhir == "✅ VALID":
                                conn.execute("INSERT OR IGNORE INTO history VALUES (?,?,?,?,?,?,?,?)",
                                            (sh, ph, uploaded.name, ws.title, f"R{row}", 
                                             str(ws.cell(row, col_c).value), str(ws.cell(row, col_s).value), 
                                             datetime.now().strftime("%Y-%m-%d")))
                            
                            all_data.append({
                                "Sheet": ws.title, "Baris": row, "Status": status_akhir, "Keterangan": detail, "Thumb": thumb
                            })
                    except: continue
            
            conn.commit()
            status.update(label="Audit Selesai!", state="complete")

        # TAMPILKAN HASIL
        if all_data:
            df_result = pd.DataFrame(all_data)
            st.subheader("Ringkasan Hasil")
            st.dataframe(df_result.drop(columns=["Thumb"]), use_container_width=True)
            
            # Download Button
            out_excel = io.BytesIO()
            df_result.drop(columns=["Thumb"]).to_excel(out_excel, index=False)
            st.download_button("📥 Download Laporan Excel", out_excel.getvalue(), "Hasil_Audit.xlsx")
            
            # Galeri Preview
            st.subheader("Preview Audit (Area Tengah)")
            cols = st.columns(4)
            for idx, r in df_result.iterrows():
                with cols[idx % 4]:
                    st.image(r["Thumb"], caption=f"{r['Status']} - {r['Sheet']} R{r['Baris']}")
        else:
            st.warning("Tidak ditemukan foto untuk diaudit di file ini.")

if os.path.exists("temp_upload.xlsx"):
    os.remove("temp_upload.xlsx")
