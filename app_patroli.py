import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Portal Patroli OSP", page_icon="🛡️", layout="wide")

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("GPSFIBEROP.xlsx")
        df.columns = df.columns.str.strip()
        return df
    except:
        return None

def save_to_log(pilihan, bulan, file_name):
    log_file = "REKAP_UPLOAD_VENDOR.xlsx"
    new_entry = pd.DataFrame([{
        "WAKTU_UPLOAD": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "BULAN_LAPORAN": bulan,
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
        st.warning("⚠️ Pastikan Anda tidak mengunggah file yang sama dengan bulan sebelumnya!")
        
        with st.form("form_upload", clear_on_submit=True):
            # 1. Pilih Segmen
            opsi = df['NO'].astype(str) + " - " + df['SEGMENT NAME']
            pilihan_final = st.selectbox("1. Pilih Segmen:", options=opsi)
            
            # 2. Pilih Bulan (Mencegah Duplikasi Lintas Bulan)
            bulan_list = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            bulan_pilih = st.selectbox("2. Laporan Untuk Bulan:", options=bulan_list)
            
            # 3. Upload File
            file_pdf = st.file_uploader("3. Upload PDF Timemark", type=["pdf"])
            
            if st.form_submit_button("KIRIM LAPORAN"):
                if file_pdf:
                    if not os.path.exists("uploads"): os.makedirs("uploads")
                    
                    # Beri nama file unik (Bulan_Segmen)
                    fname = f"LAPORAN_{bulan_pilih.upper()}_{pilihan_final.replace(' ', '_')}.pdf"
                    path_simpan = os.path.join("uploads", fname)
                    
                    # CEK DUPLIKAT: Jika file dengan nama yang sama sudah ada
                    if os.path.exists(path_simpan):
                        st.error(f"❌ GAGAL: Laporan {bulan_pilih} untuk segmen ini sudah pernah dikirim sebelumnya!")
                    else:
                        with open(path_simpan, "wb") as f:
                            f.write(file_pdf.getbuffer())
                        save_to_log(pilihan_final, bulan_pilih, fname)
                        st.success(f"✅ Berhasil! Laporan {bulan_pilih} telah tersimpan.")
                        st.balloons()
                else:
                    st.error("⚠️ Mohon lampirkan file PDF!")

    elif menu == "Admin Panel (Cek Data)":
        st.title("📊 Data Masuk & Review")
        if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
            rekap_df = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
            st.write("Cek kolom **BULAN_LAPORAN** untuk memastikan tidak ada duplikasi.")
            st.dataframe(rekap_df, use_container_width=True)
            
            st.markdown("---")
            if os.path.exists("uploads"):
                files = [f for f in os.listdir("uploads") if f.endswith('.pdf')]
                if files:
                    for f in files:
                        col1, col2 = st.columns([3, 1])
                        with col1: st.write(f"📄 {f}")
                        with col2:
                            with open(os.path.join("uploads", f), "rb") as file_data:
                                st.download_button("Lihat", data=file_data, file_name=f, key=f)
