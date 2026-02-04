elif menu == "📊 Admin Panel":
        st.title("🔐 Admin Area")
        
        # 1. Verifikasi Password
        pw = st.text_input("Password:", type="password")
        
        if pw == "indosat2024":
            st.success("Akses Diterima! Menampilkan data dan fitur kontrol.")
            
            if os.path.exists("REKAP_UPLOAD_VENDOR.xlsx"):
                rekap_df = pd.read_excel("REKAP_UPLOAD_VENDOR.xlsx")
                
                # --- FITUR RESET TABEL (DI SIDEBAR) ---
                if st.sidebar.button("🗑️ Reset Semua Rekap Tabel"):
                    os.remove("REKAP_UPLOAD_VENDOR.xlsx")
                    st.rerun()

                # --- TABEL MONITORING ---
                st.subheader("📊 Data Log Upload")
                st.dataframe(rekap_df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.subheader("📁 Manajemen & Review File")
                
                # --- DAFTAR FILE DENGAN TOMBOL DOWNLOAD & HAPUS ---
                if os.path.exists("uploads"):
                    files = [f for f in os.listdir("uploads")]
                    if files:
                        for index, f in enumerate(files):
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.write(f"📄 {f}")
                            with col2:
                                with open(os.path.join("uploads", f), "rb") as file_data:
                                    st.download_button("Download", data=file_data, file_name=f, key=f"dl_{index}")
                            with col3:
                                if st.button("Hapus", key=f"del_{index}"):
                                    os.remove(os.path.join("uploads", f))
                                    st.rerun()
                    else:
                        st.info("Folder uploads kosong.")
                else:
                    st.info("Belum ada folder uploads.")
            else:
                st.info("Belum ada catatan upload di database.")
        
        elif pw != "":
            st.error("Password Salah! Akses ditolak.")
