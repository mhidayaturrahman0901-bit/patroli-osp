import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Portal Upload Patroli OSP", layout="wide")

# 1. Fungsi Membaca File Database Utama (Excel kamu)
def load_data():
    try:
        nama_file = "GPSFIBEROP.xlsx"
        df = pd.read_excel(nama_file)
        df.columns = df.columns.str.strip() # Bersihkan nama kolom
        return df
    except Exception as e:
        st.error(f"⚠️ File '{nama_file}' tidak ditemukan atau bermasalah: {e}")
        return None

# 2. Fungsi untuk Mencatat Log ke Excel Berbeda
def save_to_log(pilihan_segmen, nama_file_saved):
    log_file = "REKAP_UPLOAD_VENDOR.xlsx"
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    data_baru = pd.DataFrame([{
        "WAKTU_UPLOAD": waktu_sekarang,
        "SEGMEN": pilihan_segmen,
        "NAMA_FILE_PDF": nama_file_saved,
        "STATUS": "BERHASIL"
    }])

    if not os.path.exists(log_file):
        data_baru.to_excel(log_file, index=False)
    else:
        with pd.ExcelWriter(log_file, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            try:
                # Ambil data lama, gabung dengan data baru
                existing_df = pd.read_excel(log_file)
                df_combined = pd.concat([existing_df, data_baru], ignore_index=True)
                df_combined.to_excel(writer, index=False)
            except:
                data_baru.to_excel(writer, index=False)

# --- MULAI TAMPILAN WEBSITE ---
df = load_data()

if df is not None:
    st.title("🛡️ Portal Pengiriman Laporan Patroli OSP")
    st.write("Gunakan tabel di bawah sebagai referensi NO dan Nama Segmen.")

    # Tampilkan Tabel (Hanya kolom yang kamu minta)
    kolom_tampil = ['NO', 'AREA', 'SEGMENT NAME']
    available_cols = [c for c in kolom_tampil if c in df.columns]
    st.dataframe(df[available_cols], use_container_width=True, hide_index=True)

    st.markdown("---")

    # Form Upload
    st.subheader("📤 Form Upload PDF Timemark")
    
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    with st.form("form_vendor"):
        # List Dropdown
        daftar_opsi = df['NO'].astype(str) + " - " + df['SEGMENT NAME']
        pilihan = st.selectbox("Pilih Segmen Jalur yang Selesai:", options=daftar_opsi)
        
        # File Input
        file_pdf = st.file_uploader("Upload PDF Timemark", type=["pdf"])
        
        btn_submit = st.form_submit_button("Kirim Laporan")

        if btn_submit:
            if file_pdf is not None:
                # Buat nama file: NO_NAMA_SEGMEN.pdf
                nama_bersih = pilihan.replace(" ", "_").replace("/", "_")
                nama_final = f"{nama_bersih}.pdf"
                path_simpan = os.path.join("uploads", nama_final)
                
                # Simpan file PDF ke folder
                with open(path_simpan, "wb") as f:
                    f.write(file_pdf.getbuffer())
                
                # CATAT KE LOG EXCEL
                save_to_log(pilihan, nama_final)
                
                st.success(f"✅ Laporan Berhasil Terkirim! Terimakasih.")
                st.balloons() # Efek perayaan kecil
            else:
                st.error("⚠️ Kamu belum memilih file PDF!")

else:
    st.warning("Pastikan file 'GPSFIBEROP.xlsx' ada di folder yang sama.")