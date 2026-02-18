import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from PIL import Image, UnidentifiedImageError
import imagehash
import io
import os
import sqlite3
import hashlib
import requests
from datetime import datetime
import re

# =========================
# CONFIG & DATABASE
# =========================
st.set_page_config(page_title="Audit Foto Patroli - Link Mode", layout="wide")
st.title("🕵️ AUDIT FOTO PATROLI (LINK GOOGLE DRIVE/DOCS)")

DB_PATH = "audit_history.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            sha256 TEXT PRIMARY KEY, phash TEXT, source_file TEXT, 
            location TEXT, first_seen DATE
        )
    """)
    return conn

# =========================
# LOGIKA DOWNLOAD & CROP
# =========================
def download_image(url):
    try:
        # Konversi link Google Drive agar bisa didownload langsung
        if 'drive.google.com' in url:
            file_id = url.split('/')[-2]
            if 'd/' in url:
                url = f'https://drive.google.com/uc?export=download&id={file_id}'
        
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.content
    except:
        return None
    return None

def audit_center_image(img_bytes):
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        w, h = img.size
        # POTONG TENGAH (Buang 25% atas/bawah untuk logo & geo)
        audit_area = img.crop((int(w*0.1), int(h*0.25), int(w*0.9), int(h*0.75)))
        
        # Hashing
        ph = str(imagehash.phash(audit_area))
        sh = hashlib.sha256(img_bytes).hexdigest()
        
        thumb = audit_area.copy()
        thumb.thumbnail((200, 200))
        return sh, ph, thumb
    except:
        return None, None, None

# =========================
# UI & PROSES
# =========================
uploaded = st.file_uploader("Upload Excel Patroli (.xlsx)", type=["xlsx"])

if uploaded:
    df = pd.read_excel(uploaded)
    st.write("Isi Excel kamu:", df.head(3))
    
    # Cari kolom Link secara otomatis
    link_col = None
    for col in df.columns:
        if "link" in str(col).lower() or "url" in str(col).lower():
            link_col = col
            break
            
    if not link_col:
        st.error("❌ Waduh, kolom 'Link' atau 'URL' gak ketemu di Excel kamu!")
    else:
        st.success(f"✅ Ketemu kolom link: **{link_col}**")
        
        if st.button("🚀 MULAI DOWNLOAD & AUDIT"):
            conn = get_db()
            results = []
            
            progress = st.progress(0)
            status_text = st.empty()
            
            for i, row in df.iterrows():
                url = str(row[link_col])
                status_text.text(f"Memproses baris ke-{i+1}...")
                
                if "http" in url:
                    raw_img = download_image(url)
                    if raw_img:
                        sh, ph, thumb = audit_center_image(raw_img)
                        if sh:
                            # Cek Duplikat
                            dup = conn.execute("SELECT source_file FROM history WHERE phash=?", (ph,)).fetchone()
                            
                            res_status = "✅ VALID"
                            if dup:
                                res_status = "❌ GUGUR (Duplikat)"
                            else:
                                conn.execute("INSERT OR IGNORE INTO history VALUES (?,?,?,?,?)",
                                            (sh, ph, uploaded.name, "Lokasi", datetime.now().date()))
                            
                            results.append({"Baris": i+1, "Link": url, "Status": res_status, "Preview": thumb})
                
                progress.progress((i + 1) / len(df))
            
            conn.commit()
            status_text.text("Audit Selesai!")
            
            # Tampilkan Hasil
            if results:
                res_df = pd.DataFrame(results)
                st.dataframe(res_df.drop(columns=["Preview"]), use_container_width=True)
                
                st.subheader("Preview Audit (Bagian Tengah Saja)")
                c = st.columns(5)
                for idx, r in res_df.iterrows():
                    with c[idx % 5]:
                        st.image(r["Preview"], caption=f"Baris {r['Baris']}")
