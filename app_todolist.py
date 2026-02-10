import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="AMF Task Dashboard", layout="wide")

# URLs
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOzwzMIUeddkwb2KcUgqBQL9rOicE7tyMM_SkxhzCO9BxO51yPm1lqk2iP9YacIsUvWBlt0IXqLAbk/pub?gid=0&single=true&output=csv"
FORM_INPUT_URL = "https://docs.google.com/forms/d/e/1FAIpQLScghNhEmaN70rFxExNB0rkZWFrY9oLwMN3Y_6TTqa-ere7Zvw/viewform"
FORM_UPDATE_BASE = "https://docs.google.com/forms/d/e/1FAIpQLScghNhEmaN70rFxExNB0rkZWFrY9oLwMN3Y_6TTqa-ere7Zvw/viewform?usp=pp_url&entry.1360407807="

# --- DATA LOADING ---
@st.cache_data(ttl=600)  # Refresh data tiap 10 menit
def load_data():
    df = pd.read_csv(CSV_URL)
    # Konversi tanggal (sesuaikan format jika perlu)
    df['Deadline'] = pd.to_datetime(df['Deadline'], dayfirst=True, errors='coerce')
    df['Bulan'] = df['Deadline'].dt.strftime('%B')
    df['Tahun'] = df['Deadline'].dt.strftime('%Y')
    return df

try:
    df_raw = load_data()
    df = df_raw.copy()

    # --- HEADER & ACTION BUTTON ---
    st.title("📋 AMF Task Monitoring Dashboard")
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        st.link_button("➕ Tambah Tugas Baru", FORM_INPUT_URL, use_container_width=True)

    # --- SECTION: TOP 3 OVERDUE & NEXT DEADLINE ---
    st.divider()
    today = datetime.now()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚨 3 Tugas Overdue")
        overdue_df = df[(df['Deadline'] < today) & (df['Status'] != 'Selesai')].sort_values('Deadline').head(3)
        if not overdue_df.empty:
            for _, row in overdue_df.iterrows():
                st.error(f"**{row['ID Tugas']}** - {row['Nama Tugas']} (Deadline: {row['Deadline'].strftime('%d %b %Y')})")
        else:
            st.success("Tidak ada tugas overdue! 🎉")

    with col2:
        st.subheader("⏳ 3 Deadline Terdekat")
        next_deadline_df = df[(df['Deadline'] >= today) & (df['Status'] != 'Selesai')].sort_values('Deadline').head(3)
        if not next_deadline_df.empty:
            for _, row in next_deadline_df.iterrows():
                st.warning(f"**{row['ID Tugas']}** - {row['Nama Tugas']} (Deadline: {row['Deadline'].strftime('%d %b %Y')})")
        else:
            st.info("Belum ada deadline mendesak.")

    # --- SIDEBAR FILTER ---
    st.sidebar.header("Filter Data")
    search = st.sidebar.text_input("Cari Nama Tugas / ID")
    
    # Filter Tahun & Bulan
    list_tahun = ["Semua"] + sorted(df['Tahun'].dropna().unique().tolist())
    selected_year = st.sidebar.selectbox("Pilih Tahun", list_tahun)
    
    list_bulan = ["Semua"] + ["January", "February", "March", "April", "May", "June", 
                              "July", "August", "September", "October", "November", "December"]
    selected_month = st.sidebar.selectbox("Pilih Bulan", list_bulan)
    
    selected_priority = st.sidebar.multiselect("Prioritas", df['Prioritas'].unique(), default=df['Prioritas'].unique())
    selected_status = st.sidebar.multiselect("Status", df['Status'].unique(), default=df['Status'].unique())

    # Apply Filters
    if search:
        df = df[df['Nama Tugas'].str.contains(search, case=False) | df['ID Tugas'].str.contains(search, case=False)]
    if selected_year != "Semua":
        df = df[df['Tahun'] == selected_year]
    if selected_month != "Semua":
        df = df[df['Bulan'] == selected_month]
    
    df = df[df['Prioritas'].isin(selected_priority)]
    df = df[df['Status'].isin(selected_status)]

# --- MAIN TABLE DENGAN FITUR KLIK ---
    st.divider()
    st.subheader(f"Daftar Tugas ({len(df)} ditemukan)")
    st.info("💡 **Tips:** Klik pada baris tabel untuk melihat Deskripsi Tugas di bawah.")

    # Menambahkan kolom link Update (untuk keperluan data)
    df['Action'] = FORM_UPDATE_BASE + df['ID Tugas'].astype(str)

    # Kolom yang akan ditampilkan di tabel
    display_cols = ['ID Tugas', 'Deadline', 'Nama Tugas', 'Kategori', 'Prioritas', 'Status', 'Action']
    
    # Membuat tabel interaktif yang bisa dipilih (selection)
    event = st.dataframe(
        df[display_cols],
        column_config={
            "Deadline": st.column_config.DateColumn("Deadline", format="DD/MM/YYYY"),
            "Action": st.column_config.LinkColumn("Update Link", display_text="Update Task ↗️"),
        },
        hide_index=True,
        use_container_width=True,
        on_select="rerun", # Menjalankan ulang script saat baris diklik
        selection_mode="single-row" # Hanya bisa pilih satu baris
    )

    # --- DETAIL DESKRIPSI (Muncul jika baris diklik) ---
    if event.selection.rows:
        selected_row_index = event.selection.rows[0]
        # Mengambil data asli berdasarkan index yang dipilih di tabel yang sudah difilter
        task_data = df.iloc[selected_row_index]
        
        st.markdown("---")
        with st.container(border=True):
            st.subheader(f"🔍 Detail: {task_data['Nama Tugas']}")
            
            col_det1, col_det2 = st.columns([1, 2])
            with col_det1:
                st.write(f"**ID Tugas:** {task_data['ID Tugas']}")
                st.write(f"**Kategori:** {task_data['Kategori']}")
                st.write(f"**Prioritas:** {task_data['Prioritas']}")
            
            with col_det2:
                st.write("**Deskripsi Tugas:**")
                # Menampilkan kolom Deskripsi dari GSheet
                deskripsi = task_data['Deskripsi'] if pd.notna(task_data['Deskripsi']) else "Tidak ada deskripsi."
                st.info(deskripsi)
                
                # Tambahan: Catatan jika ada
                if 'Catatan' in task_data and pd.notna(task_data['Catatan']):
                    st.write(f"*Catatan Tambahan:* {task_data['Catatan']}")
except Exception as e:

    st.error(f"Gagal memuat data. Pastikan link GSheet benar dan publik. Error: {e}")



