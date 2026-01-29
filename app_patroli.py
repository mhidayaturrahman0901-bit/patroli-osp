import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Portal Patroli OSP", page_icon="🛡️", layout="wide")

# Fungsi Load Data Utama
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("GPSFIBEROP.xlsx")
        df.columns = df.columns.str.strip()
        return df
    except:
        return None

# Fungsi Simpan Log
def save_to_log(pilihan, file_name):
    log_file = "REKAP_UPLOAD_VENDOR.xlsx"
    new_entry = pd.DataFrame([{
        "WAKTU_UPLOAD": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "SEGMEN": pilihan,
        "FILE_NAME": file_name
    }])
    if not os.path.exists(log_file):
        new_entry.to_excel(log_file, index=False)
    else:
        old_df = pd.read_excel(log_file)
        pd.concat([old_df, new_entry], ignore_index=True).to_excel(log_file, index=False)

# --- MENU NAVIGASI DI SIDEBAR ---
st.sidebar.title("⚙️ Control Panel")
menu = st.sidebar.radio("Pilih Halaman:", ["Upload Vendor", "Admin Panel (Cek Data)"])

df = load_data()

if df is not None:
    if menu == "Upload Vendor":
        st.title("🛡️ Portal Pengiriman Laporan Patroli OSP")
        st.info("Silakan pilih segmen dan unggah file PDF Timemark Anda.")
        
        # Tabel Referensi
        st.dataframe(df[['NO', 'AREA', 'SEGMENT NAME']], use_container_width=True, hide_index=True)

        # Form Upload
        with st.form("form_upload", clear_on_submit=True):
            opsi = df['NO'].astype(str) + " - " + df['SEGMENT NAME']
            pilihan_final = st.selectbox("Pilih Segmen:", options=opsi)
            file_pdf = st.file_uploader("Upload PDF Timemark", type=["pdf"])
            
            if st.form_submit_button("KIRIM LAPORAN"):
                if file_pdf:
                    if not os.path.exists("uploads"): os.makedirs("uploads")
                    fname = f"LAPORAN_{pilihan_final.replace(' ', '_')}.pdf"
                    path_simpan = os.path.join("uploads", fname)
                    with open(path_simpan, "wb") as f:
                        f.write(file_pdf.getbuffer())
                    save_to_log(pilihan_final, fname)
                    st.success(f"✅ Berhasil! File '{fname}' telah terkirim.")
                    st.balloons()
                else:
                    st.error("⚠️ Mohon pilih file PDF!")

    elif menu == "Admin Panel (Cek Data)":
        st.title("📊 Data Masuk Vendor")
        if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
            rekap_df = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
            st.write("Daftar laporan yang sudah masuk:")
            st.dataframe(rekap_df, use_container_width=True)
            
            st.markdown("---")
            st.subheader("📁 Download File PDF")
            if os.path.exists("uploads"):
                files = [f for f in os.listdir("uploads") if f.endswith('.pdf')]
                if files:
                    for f in files:
                        with open(os.path.join("uploads", f), "rb") as file_data:
                            st.download_button(label=f"📥 Download {f}", data=file_data, file_name=f, key=f)
                else:
                    st.warning("Belum ada file PDF di folder uploads.")
        else:
            st.info("Belum ada aktivitas upload.")
else:
    st.error("File database tidak ditemukan!")
