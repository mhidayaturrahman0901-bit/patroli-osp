import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Portal Patroli OSP Indosat", page_icon="🛡️", layout="wide")

# Fungsi untuk memuat database Excel segmen
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("GPSFIBEROP.xlsx")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Gagal memuat file database: {e}")
        return None

# Fungsi untuk mencatat log upload ke Excel
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

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("⚙️ Control Panel")
menu = st.sidebar.radio("Pilih Halaman:", ["📤 Upload Vendor", "📊 Admin Panel (Cek Data)"])

df_master = load_data()

if df_master is not None:
    # --- HALAMAN 1: UPLOAD VENDOR ---
    if menu == "📤 Upload Vendor":
        st.title("🛡️ Portal Pengiriman Laporan Patroli OSP")
        st.info("Pilih bulan dan segmen dengan benar sebelum mengunggah file PDF.")

        with st.form("form_upload", clear_on_submit=True):
            # Input 1: Pilih Segmen
            opsi_segmen = df_master['NO'].astype(str) + " - " + df_master['SEGMENT NAME']
            pilihan_segmen = st.selectbox("1. Pilih Segmen Patroli:", options=opsi_segmen)
            
            # Input 2: Pilih Bulan
            list_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            pilihan_bulan = st.selectbox("2. Laporan Untuk Bulan:", options=list_bulan)
            
            # Input 3: Pilih File
            file_pdf = st.file_uploader("3. Upload PDF Timemark", type=["pdf"])
            
            submit = st.form_submit_button("KIRIM LAPORAN")
            
            if submit:
                if file_pdf:
                    if not os.path.exists("uploads"):
                        os.makedirs("uploads")
                    
                    # Format nama file: LAPORAN_BULAN_SEGMEN.pdf
                    nama_file_bersih = pilihan_segmen.replace(" ", "_").replace("/", "-")
                    fname = f"LAPORAN_{pilihan_bulan.upper()}_{nama_file_bersih}.pdf"
                    path_simpan = os.path.join("uploads", fname)
                    
                    # CEK DUPLIKAT (Mencegah upload ulang di bulan yang sama)
                    if os.path.exists(path_simpan):
                        st.error(f"❌ GAGAL: Laporan bulan {pilihan_bulan} untuk segmen ini sudah ada!")
                    else:
                        with open(path_simpan, "wb") as f:
                            f.write(file_pdf.getbuffer())
                        save_to_log(pilihan_segmen, pilihan_bulan, fname)
                        st.success(f"✅ Berhasil Terkirim!")
                        st.balloons()
                else:
                    st.error("⚠️ File PDF wajib dilampirkan!")

    # --- HALAMAN 2: ADMIN PANEL (DENGAN PASSWORD) ---
    elif menu == "📊 Admin Panel (Cek Data)":
        st.title("🔐 Akses Admin Terbatas")
        
        # INPUT PASSWORD
        password_input = st.text_input("Masukkan Password Admin:", type="password")
        
        if password_input == "indosat2024":
            st.success("Akses Diterima!")
            st.markdown("---")
            
            # FITUR RESET REKAP DI SIDEBAR
            if st.sidebar.button("🗑️ Reset Semua Rekap Tabel"):
                if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
                    os.remove("REKAP_UPLOAD_VENDOR.xlsx")
                    st.rerun()

            # TAMPILKAN TABEL REKAP
            if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
                rekap_df = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
                
                # FILTER BULAN
                st.subheader("🔍 Filter Data Laporan")
                bulan_pilihan = ["Semua Bulan", "Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                                 "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
                filter_bln = st.selectbox("Tampilkan laporan bulan:", options=bulan_pilihan)
                
                if filter_bln != "Semua Bulan":
                    df_final = rekap_df[rekap_df['BULAN_LAPORAN'] == filter_bln]
                else:
                    df_final = rekap_df

                st.dataframe(df_final, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.subheader(f"📁 Manajemen File ({filter_bln})")
                
                # DAFTAR FILE DAN TOMBOL HAPUS
                if not df_final.empty:
                    for index, row in df_final.iterrows():
                        f_name = row['FILE_NAME']
                        f_path = os.path.join("uploads", f_name)
                        
                        if os.path.exists(f_path):
                            c1, c2, c3 = st.columns([3, 1, 1])
                            with c1:
                                st.write(f"📄 {f_name}")
                            with c2:
                                with open(f_path, "rb") as fl:
                                    st.download_button("Lihat", data=fl, file_name=f_name, key=f"dl_{index}")
                            with c3:
                                if st.button("Hapus", key=f"del_{index}"):
                                    os.remove(f_path)
                                    st.rerun()
                else:
                    st.info(f"Tidak ada file untuk bulan {filter_bln}")
            else:
                st.info("Belum ada data upload yang masuk.")
                
        elif password_input != "":
            st.error("Password Salah! Akses ditolak.")

else:
    st.error("File GPSFIBEROP.xlsx tidak ditemukan. Pastikan file ada di GitHub.")

