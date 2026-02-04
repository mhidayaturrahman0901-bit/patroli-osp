import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Portal Patroli OSP Indosat", page_icon="🛡️", layout="wide")

# Fungsi hitung sidik jari file (HASH)
def calculate_hash(file):
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    file.seek(0)
    return sha256_hash.hexdigest()

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("GPSFIBEROP.xlsx")
        df.columns = df.columns.str.strip()
        return df
    except: return None

def save_to_log(pilihan, bulan, file_name, file_hash):
    log_file = "REKAP_UPLOAD_VENDOR.xlsx"
    new_entry = pd.DataFrame([{
        "WAKTU_UPLOAD": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "BULAN_LAPORAN": bulan,
        "SEGMEN": pilihan,
        "FILE_NAME": file_name,
        "FILE_HASH": file_hash
    }])
    if not os.path.exists(log_file):
        new_entry.to_excel(log_file, index=False)
    else:
        old_df = pd.read_excel(log_file)
        pd.concat([old_df, new_entry], ignore_index=True).to_excel(log_file, index=False)

# --- NAVIGASI ---
st.sidebar.title("⚙️ Control Panel")
menu = st.sidebar.radio("Pilih Halaman:", ["📤 Upload Vendor", "📊 Admin Panel"])

df_master = load_data()

if df_master is not None:
    if menu == "📤 Upload Vendor":
        st.title("🛡️ Portal Patroli OSP")
        st.warning("Sistem mendeteksi duplikasi foto secara otomatis.")

        with st.form("form_upload", clear_on_submit=True):
            opsi_segmen = df_master['NO'].astype(str) + " - " + df_master['SEGMENT NAME']
            pilihan_segmen = st.selectbox("1. Pilih Segmen:", options=opsi_segmen)
            list_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            pilihan_bulan = st.selectbox("2. Bulan:", options=list_bulan)
            file_pdf = st.file_uploader("3. Upload PDF", type=["pdf"])
            submit = st.form_submit_button("KIRIM LAPORAN")
            
            if submit and file_pdf:
                current_file_hash = calculate_hash(file_pdf)
                
                # Cek Duplikasi Isi
                is_duplicate_content = False
                if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
                    rekap_existing = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
                    if 'FILE_HASH' in rekap_existing.columns:
                        if current_file_hash in rekap_existing['FILE_HASH'].values:
                            is_duplicate_content = True

                if is_duplicate_content:
                    st.error("❌ GAGAL: Isi file/foto ini sudah pernah diunggah sebelumnya! Gunakan foto patroli terbaru.")
                else:
                    if not os.path.exists("uploads"): os.makedirs("uploads")
                    nama_bersih = pilihan_segmen.replace(" ", "_").replace("/", "-")
                    fname = f"LAPORAN_{pilihan_bulan.upper()}_{nama_bersih}.pdf"
                    
                    with open(os.path.join("uploads", fname), "wb") as f:
                        f.write(file_pdf.getbuffer())
                    
                    save_to_log(pilihan_segmen, pilihan_bulan, fname, current_file_hash)
                    st.success("✅ Berhasil! File divalidasi dan tersimpan.")
                    st.balloons()

    elif menu == "📊 Admin Panel":
        st.title("🔐 Admin Area")
        pw = st.text_input("Password:", type="password")
        if pw == "indosat2024":
            if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
                rekap_df = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
                st.dataframe(rekap_df, use_container_width=True)
                
                # Tambahkan tombol hapus/reset jika perlu seperti kemarin
            else:
                st.info("Belum ada data.")
