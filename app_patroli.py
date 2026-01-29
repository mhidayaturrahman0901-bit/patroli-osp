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
        # Membersihkan nama kolom dari spasi tambahan
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Gagal memuat file Excel: {e}")
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
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/a/ac/Indosat_Ooredoo_Hutchison_logo.svg", width=150) # Opsional: Logo Indosat
st.sidebar.title("⚙️ Control Panel")
menu = st.sidebar.radio("Pilih Halaman:", ["📤 Upload Vendor", "📊 Admin Panel (Cek Data)"])

df_master = load_data()

if df_master is not None:
    # --- HALAMAN 1: UPLOAD VENDOR ---
    if menu == "📤 Upload Vendor":
        st.title("🛡️ Portal Pengiriman Laporan Patroli OSP")
        st.info("Silakan pilih bulan, segmen, dan unggah file PDF laporan Anda.")

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
                    # Buat folder uploads jika belum ada
                    if not os.path.exists("uploads"):
                        os.makedirs("uploads")
                    
                    # Buat nama file unik: LAPORAN_BULAN_SEGMEN.pdf
                    nama_file_bersih = pilihan_segmen.replace(" ", "_").replace("/", "-")
                    fname = f"LAPORAN_{pilihan_bulan.upper()}_{nama_file_bersih}.pdf"
                    path_simpan = os.path.join("uploads", fname)
                    
                    # CEK DUPLIKAT
                    if os.path.exists(path_simpan):
                        st.error(f"❌ GAGAL: Laporan bulan {pilihan_bulan} untuk segmen ini sudah ada di server!")
                    else:
                        with open(path_simpan, "wb") as f:
                            f.write(file_pdf.getbuffer())
                        save_to_log(pilihan_segmen, pilihan_bulan, fname)
                        st.success(f"✅ Berhasil! Laporan {pilihan_bulan} untuk {pilihan_segmen} telah tersimpan.")
                        st.balloons()
                else:
                    st.error("⚠️ Mohon pilih file PDF terlebih dahulu!")

    # --- HALAMAN 2: ADMIN PANEL ---
    elif menu == "📊 Admin Panel (Cek Data)":
        st.title("📊 Dashboard Monitoring Admin")
        
        # Tombol Reset Tabel (Hanya jika file Excel log ada)
        if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
            if st.sidebar.button("🗑️ Reset Tabel Rekap"):
                os.remove("REKAP_UPLOAD_VENDOR.xlsx")
                st.rerun()

        # Menampilkan Tabel Rekap dengan Filter Bulan
        if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
            rekap_df = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
            
            st.subheader("🔍 Filter & Cari Data")
            filter_bulan = st.selectbox("Filter Tampilan Berdasarkan Bulan:", 
                                       ["Semua Bulan"] + ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                                                        "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            
            if filter_bulan != "Semua Bulan":
                df_tampil = rekap_df[rekap_df['BULAN_LAPORAN'] == filter_bulan]
            else:
                df_tampil = rekap_df

            st.dataframe(df_tampil, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader(f"📁 Manajemen File PDF ({filter_bulan})")
            
            if not df_tampil.empty:
                for index, row in df_tampil.iterrows():
                    f_name = row['FILE_NAME']
                    f_path = os.path.join("uploads", f_name)
                    
                    if os.path.exists(f_path):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"📄 {f_name}")
                        with col2:
                            with open(f_path, "rb") as f_data:
                                st.download_button("Download", data=f_data, file_name=f_name, key=f"dl_{index}")
                        with col3:
                            if st.button("Hapus", key=f"del_{index}"):
                                os.remove(f_path)
                                st.rerun()
                    else:
                        st.warning(f"File {f_name} sudah tidak ada di folder uploads.")
            else:
                st.info(f"Tidak ada file PDF untuk bulan {filter_bulan}.")
        else:
            st.info("Belum ada data upload yang masuk.")

else:
    st.error("Sistem Error: File GPSFIBEROP.xlsx tidak ditemukan di repository GitHub Anda.")
