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

# --- MENU NAVIGASI ---
st.sidebar.title("⚙️ Control Panel")
menu = st.sidebar.radio("Pilih Halaman:", ["Upload Vendor", "Admin Panel (Cek Data)"])

df = load_data()

if df is not None:
    if menu == "Upload Vendor":
        st.title("🛡️ Portal Pengiriman Laporan Patroli OSP")
        st.info("Pilih segmen dan unggah file PDF Timemark Anda.")
        
        st.dataframe(df[['NO', 'AREA', 'SEGMENT NAME']], use_container_width=True, hide_index=True)

        with st.form("form_upload", clear_on_submit=True):
            opsi = df['NO'].astype(str) + " - " + df['SEGMENT NAME']
            pilihan_final = st.selectbox("Pilih Segmen:", options=opsi)
            file_pdf = st.file_uploader("Upload PDF Timemark", type=["pdf"])
            
            if st.form_submit_button("KIRIM LAPORAN"):
                if file_pdf:
                    if not os.path.exists("uploads"): os.makedirs("uploads")
                    fname = f"LAPORAN_{pilihan_final.replace(' ', '_')}.pdf"
                    with open(os.path.join("uploads", fname), "wb") as f:
                        f.write(file_pdf.getbuffer())
                    save_to_log(pilihan_final, fname)
                    st.success(f"✅ Berhasil! Laporan tersimpan.")
                    st.balloons()
                else:
                    st.error("⚠️ Lampirkan file PDF!")

    elif menu == "Admin Panel (Cek Data)":
        st.title("📊 Data Masuk & Review Laporan")
        if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
            rekap_df = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
            st.dataframe(rekap_df, use_container_width=True)
            
            st.markdown("---")
            st.subheader("📁 Review & Download Foto")
            
            if os.path.exists("uploads"):
                files = [f for f in os.listdir("uploads") if f.endswith('.pdf')]
                if files:
                    # Menampilkan daftar file dengan tombol yang jelas
                    for f in files:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"📄 {f}")
                        with col2:
                            with open(os.path.join("uploads", f), "rb") as file_data:
                                st.download_button(
                                    label="Lihat / Download",
                                    data=file_data,
                                    file_name=f,
                                    key=f,
                                    mime="application/pdf"
                                )
                else:
                    st.warning("Belum ada file di server.")
        else:
            st.info("Belum ada data upload.")
else:
    st.error("Database tidak ditemukan!")
