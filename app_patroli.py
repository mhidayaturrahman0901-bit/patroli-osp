import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Portal Patroli OSP Indosat", page_icon="🛡️", layout="wide")

# Fungsi hitung sidik jari file (HASH) untuk deteksi duplikasi isi
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
    except:
        return None

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

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("⚙️ Control Panel")
menu = st.sidebar.radio("Pilih Halaman:", ["📤 Upload Vendor", "📊 Admin Panel"])

df_master = load_data()

if df_master is not None:
    # --- HALAMAN 1: UPLOAD VENDOR ---
    if menu == "📤 Upload Vendor":
        st.title("🛡️ Portal Pengiriman Laporan Patroli OSP")
        st.info("Sistem mendeteksi duplikasi foto secara otomatis menggunakan SHA-256 Hashing.")

        with st.form("form_upload", clear_on_submit=True):
            opsi_segmen = df_master['NO'].astype(str) + " - " + df_master['SEGMENT NAME']
            pilihan_segmen = st.selectbox("1. Pilih Segmen:", options=opsi_segmen)
            
            list_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            pilihan_bulan = st.selectbox("2. Laporan Untuk Bulan:", options=list_bulan)
            
            file_pdf = st.file_uploader("3. Upload PDF Timemark", type=["pdf"])
            
            if st.form_submit_button("KIRIM LAPORAN"):
                if file_pdf:
                    current_hash = calculate_hash(file_pdf)
                    
                    # Cek Duplikasi Isi File di Log Excel
                    is_duplicate = False
                    if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
                        log_df = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
                        if 'FILE_HASH' in log_df.columns and current_hash in log_df['FILE_HASH'].values:
                            is_duplicate = True

                    if is_duplicate:
                        st.error("❌ GAGAL: Isi file/foto ini sudah pernah diunggah sebelumnya! Gunakan foto terbaru.")
                    else:
                        if not os.path.exists("uploads"): os.makedirs("uploads")
                        fname = f"LAPORAN_{pilihan_bulan.upper()}_{pilihan_segmen.replace(' ', '_')}.pdf"
                        
                        with open(os.path.join("uploads", fname), "wb") as f:
                            f.write(file_pdf.getbuffer())
                        
                        save_to_log(pilihan_segmen, pilihan_bulan, fname, current_hash)
                        st.success("✅ Berhasil! File unik telah divalidasi dan tersimpan.")
                        st.balloons()
                else:
                    st.error("⚠️ Mohon lampirkan file PDF!")

    # --- HALAMAN 2: ADMIN PANEL ---
    elif menu == "📊 Admin Panel":
        st.title("🔐 Admin Area")
        pw = st.text_input("Masukkan Password Admin:", type="password")
        
        if pw == "indosat2024":
            st.success("Akses Diterima!")
            
            if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
                rekap_df = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
                
                # Tombol Reset Tabel di Sidebar
                if st.sidebar.button("🗑️ Reset Semua Rekap Tabel"):
                    os.remove("REKAP_UPLOAD_VENDOR.xlsx")
                    st.rerun()

                st.subheader("📊 Tabel Log Rekap")
                st.dataframe(rekap_df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.subheader("📁 Manajemen File PDF")
                
                if os.path.exists("uploads"):
                    files = [f for f in os.listdir("uploads")]
                    if files:
                        for i, f in enumerate(files):
                            c1, c2, c3 = st.columns([3, 1, 1])
                            with c1: st.write(f"📄 {f}")
                            with c2:
                                with open(os.path.join("uploads", f), "rb") as d:
                                    st.download_button("Download", data=d, file_name=f, key=f"dl_{i}")
                            with c3:
                                if st.button("Hapus", key=f"del_{i}"):
                                    os.remove(os.path.join("uploads", f))
                                    st.rerun()
                    else: st.info("Folder uploads kosong.")
            else: st.info("Belum ada data upload.")
        elif pw != "":
            st.error("Password Salah!")

else:
    st.error("File GPSFIBEROP.xlsx tidak ditemukan!")
