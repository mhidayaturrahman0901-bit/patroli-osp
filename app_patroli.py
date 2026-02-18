import streamlit as st
import pandas as pd
from PIL import Image
import imagehash
import io
import os
import sqlite3
import hashlib
import requests
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Audit Foto - Google Docs Mode", layout="wide")
st.title("🕵️ AUDIT FOTO (LINK GOOGLE DOCS)")
st.info("Kodingan ini akan mencoba mengambil gambar dari link Google Docs di Excel kamu.")

# =========================
# FUNGSI DOWNLOAD DOCS
# =========================
def get_image_from_docs(url):
    try:
        # Jika link Google Docs, kita coba convert ke mode export
        if 'docs.google.com/document' in url:
            # Mengubah /edit menjadi /export?format=pdf untuk ekstraksi (trik bypass)
            export_url = url.replace('/edit', '/export?format=png') 
            # Note: Docs tidak selalu izinkan export png langsung, 
            # Jika gagal, kita butuh penanganan lebih lanjut
            r = requests.get(export_url, timeout=15)
            if r.status_code == 200:
                return r.content
        return None
    except:
        return None

def audit_process(img_bytes):
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        w, h = img.size
        # POTONG TENGAH (Buang logo atas & geo bawah)
        audit_area = img.crop((int(w*0.1), int(h*0.25), int(w*0.9), int(h*0.75)))
        
        ph = str(imagehash.phash(audit_area))
        sh = hashlib.sha256(img_bytes).hexdigest()
        
        thumb = audit_area.copy()
        thumb.thumbnail((150, 150))
        return sh, ph, thumb
    except:
        return None, None, None

# =========================
# UI ACTION
# =========================
uploaded = st.file_uploader("Upload Excel", type=["xlsx"])

if uploaded:
    df = pd.read_excel(uploaded)
    # Cari kolom yang isinya link Docs (biasanya di kolom G atau L di screenshotmu)
    target_col = None
    for col in df.columns:
        if df[col].astype(str).str.contains('docs.google.com').any():
            target_col = col
            break
    
    if target_col:
        st.success(f"Ditemukan kolom link: **{target_col}**")
        if st.button("🚀 PROSES AUDIT DARI GOOGLE DOCS"):
            results = []
            conn = sqlite3.connect("audit_history.db")
            
            for i, row in df.iterrows():
                url = str(row[target_col])
                if 'http' in url:
                    with st.spinner(f"Mendownload foto baris {i+1}..."):
                        img_data = get_image_from_docs(url)
                        if img_data:
                            sh, ph, thumb = audit_process(img_data)
                            if ph:
                                # Cek database
                                res = conn.execute("SELECT first_seen FROM history WHERE phash=?", (ph,)).fetchone()
                                status = "✅ VALID" if not res else "❌ GUGUR"
                                
                                if status == "✅ VALID":
                                    conn.execute("INSERT OR IGNORE INTO history VALUES (?,?,?,?,?)", 
                                               (sh, ph, "Docs", url, datetime.now().date()))
                                
                                results.append({"Baris": i+1, "Status": status, "Preview": thumb})
                                st.image(thumb, caption=f"Baris {i+1}: {status}")
            conn.commit()
    else:
        st.error("Kolom berisi link Google Docs tidak ditemukan!")
