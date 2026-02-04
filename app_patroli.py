import streamlit as st
import pandas as pd
import os
import hashlib
import sqlite3
import io
import imagehash
from PIL import Image
from openpyxl import load_workbook
from datetime import datetime

# --- 1. KONFIGURASI & DATABASE ---
st.set_page_config(page_title="Portal Patroli OSP & Audit", page_icon="🛡️", layout="wide")

def get_db_connection():
    conn = sqlite3.connect('master_audit.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS history 
                   (hash TEXT PRIMARY KEY, segment TEXT, file_name TEXT, date TEXT)''')
    return conn

# Fungsi hash untuk file (PDF/Excel)
def calculate_file_hash(file):
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    file.seek(0)
    return sha256_hash.hexdigest()

# --- 2. ENGINE AUDIT FOTO (DALAM EXCEL) ---
def run_photo_audit(file_path):
    wb = load_workbook(file_path, data_only=True)
    photo_results = []
    conn = get_db_connection()
    
    for sheet in wb.worksheets:
        if hasattr(sheet, '_images'):
            for img_obj in sheet._images:
                try:
                    row = img_obj.anchor._from.row + 1
                    col = img_obj.anchor._from.col + 1
                    segment = sheet.cell(row=row, column=3).value or "N/A"
                    
                    # Convert image data to hash
                    img = Image.open(io.BytesIO(img_obj._data())).convert('RGB')
                    p_hash = str(imagehash.phash(img)) # Digital Fingerprint Foto
                    
                    # Cek Lintas Periode di Database
                    res = conn.execute("SELECT date FROM history WHERE hash=?", (p_hash,)).fetchone()
                    
                    status = "✅ VALID (FOTO BARU)"
                    if res:
                        status = f"❌ GUGUR (Pernah Terbit: {res[0]})"
                    
                    photo_results.append({
                        "Sheet": sheet.title,
                        "Posisi": f"Baris {row}, Kolom {col}",
                        "Segmen": segment,
                        "Photo_Hash": p_hash,
                        "Status_Audit": status
                    })
                except: continue
    return photo_results

# --- 3. UI SIDEBAR ---
st.sidebar.title("🛡️ OSP CONTROL")
menu = st.sidebar.radio("Menu Utama:", ["📤 Upload Vendor", "📊 Admin Panel & Audit"])

# --- 4. HALAMAN UPLOAD VENDOR ---
if menu == "📤 Upload Vendor":
    st.title("📤 Pengiriman Laporan Patroli")
    st.info("Sistem mengaudit duplikasi file dan isi foto secara otomatis.")

    try:
        df_master = pd.read_excel("GPSFIBEROP.xlsx")
        opsi_segmen = df_master['NO'].astype(str) + " - " + df_master['SEGMENT NAME'].str.strip()
        
        col1, col2 = st.columns(2)
        with col1:
            bulan = st.selectbox("Laporan Bulan:", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
        with col2:
            segmen = st.selectbox("Pilih Segmen:", opsi_segmen)

        file_input = st.file_uploader("Upload File (PDF/Excel):", type=["pdf", "xlsx", "xls"])

        if file_input:
            f_hash = calculate_file_hash(file_input)
            
            # Cek duplikat file di log Excel
            is_dup_file = False
            if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
                rekap_check = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
                if 'HASH' in rekap_check.columns and f_hash in rekap_check['HASH'].values:
                    is_dup_file = True

            if is_dup_file:
                st.error("❌ File ini sudah pernah diunggah! Harap gunakan file laporan terbaru.")
            else:
                if st.button("🚀 KIRIM LAPORAN SEKARANG"):
                    if not os.path.exists("uploads"): os.makedirs("uploads")
                    ext = os.path.splitext(file_input.name)[1]
                    fname = f"{bulan.upper()}_{segmen.replace(' ', '_')}{ext}"
                    path = os.path.join("uploads", fname)
                    
                    with open(path, "wb") as f:
                        f.write(file_input.getbuffer())
                    
                    # Simpan ke Log
                    log_data = pd.DataFrame([{"WAKTU": datetime.now().strftime("%Y-%m-%d %H:%M"), "BULAN": bulan, "SEGMEN": segmen, "FILE": fname, "HASH": f_hash}])
                    if not os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
                        log_data.to_excel("REKAP_UPLOAD_VENDOR.xlsx", index=False)
                    else:
                        old_log = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
                        pd.concat([old_log, log_data], ignore_index=True).to_excel("REKAP_UPLOAD_VENDOR.xlsx", index=False)
                    
                    st.success("✅ Berhasil! Laporan Anda telah masuk ke sistem audit.")
                    st.balloons()
    except:
        st.error("File GPSFIBEROP.xlsx tidak ditemukan!")

# --- 5. HALAMAN ADMIN & HASIL AUDIT ---
elif menu == "📊 Admin Panel & Audit":
    st.title("📊 Monitoring & Audit Lintas Periode")
    if st.text_input("Password Admin:", type="password") == "indosat2024":
        
        if os.path.exists("uploads"):
            files = os.listdir("uploads")
            selected_file = st.selectbox("Pilih File yang Ingin Diaudit Fotonya:", files)
            
            if st.button("🔍 JALANKAN AUDIT FOTO"):
                file_path = os.path.join("uploads", selected_file)
                
                if ".xlsx" in selected_file:
                    with st.spinner("Sedang membedah isi foto..."):
                        audit_data = run_photo_audit(file_path)
                        
                        if audit_data:
                            df_audit = pd.DataFrame(audit_data)
                            st.dataframe(df_audit, use_container_width=True)
                            
                            # Update History Database untuk foto yang VALID
                            conn = get_db_connection()
                            curr_date = datetime.now().strftime("%Y-%m-%d")
                            for _, r in df_audit.iterrows():
                                if "VALID" in r['Status_Audit']:
                                    try:
                                        conn.execute("INSERT INTO history VALUES (?,?,?,?)", 
                                                     (r['Photo_Hash'], r['Segmen'], selected_file, curr_date))
                                    except: pass
                            conn.commit()

                            # DOWNLOAD HASIL AUDIT
                            output = io.BytesIO()
                            df_audit.to_excel(output, index=False)
                            st.download_button("📥 DOWNLOAD HASIL AUDIT (EXCEL)", output.getvalue(), f"Hasil_Audit_{selected_file}.xlsx")
                        else:
                            st.warning("Tidak ditemukan foto yang menempel (embedded) di file Excel ini.")
                else:
                    st.info("Fitur Audit Foto mendalam saat ini khusus untuk file .xlsx. Untuk PDF, silakan cek manual lewat tombol Download.")

            st.markdown("---")
            st.subheader("Manajemen File Uploads")
            for i, f in enumerate(files):
                c1, c2, c3 = st.columns([3,1,1])
                c1.write(f"📄 {f}")
                c2.download_button("Download", open(os.path.join("uploads", f), "rb"), file_name=f, key=f"dl{i}")
                if c3.button("Hapus", key=f"del{i}"):
                    os.remove(os.path.join("uploads", f))
                    st.rerun()
