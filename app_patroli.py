import streamlit as st
import pandas as pd
import os
import base64
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

# Fungsi untuk menampilkan PDF
def displayPDF(file):
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- MENU NAVIGASI ---
st.sidebar.title("⚙️ Control Panel")
menu = st.sidebar.radio("Pilih Halaman:", ["Upload Vendor", "Admin Panel (Cek Data)"])

df = load_data()

if df is not None:
    if menu == "Upload Vendor":
        st.title("🛡️ Portal Pengiriman Laporan Patroli OSP")
        st.info("Silakan pilih segmen dan unggah file PDF Timemark Anda.")
        
        st.dataframe(df[['NO', 'AREA', 'SEGMENT NAME']], use_container_width=True, hide_index=True)

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
                    st.success(f"✅ Berhasil Terkirim!")
                    st.balloons()
                else:
                    st.error("⚠️ Pilih file PDF dulu!")

    elif menu == "Admin Panel (Cek Data)":
        st.title("📊 Data Masuk & Pratinjau Foto")
        if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
            rekap_df = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
            st.dataframe(rekap_df, use_container_width=True)
            
            st.markdown("---")
            
            # FITUR PREVIEW
            if os.path.exists("uploads"):
                list_files = [f for f in os.listdir("uploads") if f.endswith('.pdf')]
                if list_files:
                    st.subheader("🔍 Intip Isi Laporan (Foto)")
                    file_terpilih = st.selectbox("Pilih file yang mau dilihat:", list_files)
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        path_file = os.path.join("uploads", file_terpilih)
                        with open(path_file, "rb") as f:
                            st.download_button("📥 Download File Ini", data=f, file_name=file_terpilih)
                    
                    with col2:
                        st.write(f"Menampilkan: {file_terpilih}")
                        displayPDF(path_file)
                else:
                    st.warning("Belum ada file PDF untuk dilihat.")
        else:
            st.info("Belum ada aktivitas upload.")
else:
    st.error("File database tidak ditemukan!")
