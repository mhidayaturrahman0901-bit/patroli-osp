import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime

# 1. SETUP
st.set_page_config(page_title="Upload Laporan OSP", page_icon="🛡️")

def calculate_hash(file):
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    file.seek(0)
    return sha256_hash.hexdigest()

def save_to_log(pilihan, bulan, file_name, file_hash):
    log_file = "REKAP_UPLOAD_VENDOR.xlsx"
    new_entry = pd.DataFrame([{"WAKTU": datetime.now().strftime("%d/%m %H:%M"), "BULAN": bulan, "SEGMEN": pilihan, "FILE": file_name, "HASH": file_hash}])
    if not os.path.exists(log_file):
        new_entry.to_excel(log_file, index=False)
    else:
        old_df = pd.read_excel(log_file)
        pd.concat([old_df, new_entry], ignore_index=True).to_excel(log_file, index=False)

# --- SIDEBAR ---
menu = st.sidebar.radio("Menu:", ["📤 Upload Vendor", "📊 Admin Panel"])

# --- HALAMAN UPLOAD (DISEDERHANAKAN) ---
if menu == "📤 Upload Vendor":
    st.title("🛡️ Portal Laporan OSP")
    
    try:
        df_master = pd.read_excel("GPSFIBEROP.xlsx")
        opsi_segmen = df_master['NO'].astype(str) + " - " + df_master['SEGMENT NAME'].str.strip()
        
        col1, col2 = st.columns(2)
        with col1:
            bulan = st.selectbox("Pilih Bulan:", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
        with col2:
            segmen = st.selectbox("Pilih Segmen:", opsi_segmen)

        # File uploader tanpa Form (Langsung Proses)
        file_pdf = st.file_uploader("Upload PDF Timemark di sini:", type=["pdf"])

        if file_pdf is not None:
            current_hash = calculate_hash(file_pdf)
            
            # Cek Duplikat Isi
            is_dup = False
            if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
                log_df = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
                if 'HASH' in log_df.columns and current_hash in log_df['HASH'].values:
                    is_dup = True

            if is_dup:
                st.error("❌ File ini sudah pernah diupload sebelumnya. Harap gunakan foto terbaru!")
            else:
                if st.button("KONFIRMASI KIRIM"): # Satu klik terakhir untuk kepastian
                    if not os.path.exists("uploads"): os.makedirs("uploads")
                    fname = f"{bulan.upper()}_{segmen.replace(' ', '_')}.pdf"
                    with open(os.path.join("uploads", fname), "wb") as f:
                        f.write(file_pdf.getbuffer())
                    save_to_log(segmen, bulan, fname, current_hash)
                    st.success(f"✅ Berhasil Terkirim!")
                    st.balloons()
    except:
        st.error("File GPSFIBEROP.xlsx tidak ditemukan!")

# --- HALAMAN ADMIN (TETAP AMAN) ---
elif menu == "📊 Admin Panel":
    st.title("🔐 Admin Area")
    if st.text_input("Password:", type="password") == "indosat2024":
        if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
            rekap = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
            st.dataframe(rekap, use_container_width=True)
            
            st.markdown("---")
            if os.path.exists("uploads"):
                files = os.listdir("uploads")
                for i, f in enumerate(files):
                    c1, c2, c3 = st.columns([3,1,1])
                    c1.write(f)
                    c2.download_button("☁️", open(os.path.join("uploads", f), "rb"), file_name=f, key=f"dl{i}")
                    if c3.button("🗑️", key=f"del{i}"):
                        os.remove(os.path.join("uploads", f))
                        st.rerun()
        else:
            st.info("Belum ada data.")
