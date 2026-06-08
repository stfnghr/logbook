import streamlit as st
import re
import pandas as pd
from datetime import datetime

# Setup Halaman UI
st.set_page_config(page_title="Viewer Logbook Magang", page_icon="💬", layout="centered")
st.title("Logbook Chat Viewer (13:30 - 17:30)")
st.caption("Pilih bulan dan tanggal di panel sebelah kiri untuk menganalisis aktivitas harian.")

# Regex untuk membaca format waktu iOS WhatsApp
pattern = re.compile(r'^\[(\d{2})/(\d{2})/(\d{2}), (\d{2})\.(\d{2})\.(\d{2})\] (.*?): (.*)')

@st.cache_data
def get_filtered_chat():
    chat_list = []
    include_msg = False
    
    try:
        with open('_chat.txt', 'r', encoding='utf-8') as f:
            for line in f:
                # Membersihkan karakter tersembunyi
                line = line.replace('\u200e', '').replace('\u200f', '').strip()
                if not line: continue
                
                match = pattern.search(line)
                if match:
                    d, m, y, h, mn, s, sender, msg = match.groups()
                    y, m, d, h, mn = int(y), int(m), int(d), int(h), int(mn)
                    
                    # Filter: Tahun 2026 ke atas, mulai bulan Maret
                    if (y == 26 and m >= 3) or (y > 26):
                        # Filter Waktu Jam Magang
                        time_valid = False
                        if h == 13 and mn >= 30: time_valid = True
                        elif 14 <= h <= 16: time_valid = True
                        elif h == 17 and mn <= 30: time_valid = True
                        
                        if time_valid:
                            date_str = f"20{y}-{m:02d}-{d:02d}"
                            time_str = f"{h:02d}:{mn:02d}"
                            chat_list.append({
                                "date": date_str,
                                "time": time_str,
                                "sender": sender,
                                "message": msg
                            })
                            include_msg = True
                        else:
                            include_msg = False
                    else:
                        include_msg = False
                else:
                    # Menangani pesan multiline (enter)
                    if include_msg and chat_list:
                        chat_list[-1]["message"] += f"\n{line}"
                        
    except FileNotFoundError:
        st.error("File '_chat.txt' tidak ditemukan. Pastikan ada di folder yang sama!")
        return pd.DataFrame()
        
    df = pd.DataFrame(chat_list)
    if not df.empty:
        # Konversi string ke format datetime untuk kemudahan UI
        df['date_obj'] = pd.to_datetime(df['date'])
        df['Bulan'] = df['date_obj'].dt.strftime('%B %Y')
    return df

# Memuat Data
df = get_filtered_chat()

if df.empty:
    st.warning("Belum ada data yang bisa ditampilkan.")
else:
    # --- SIDEBAR UI ---
    st.sidebar.header("Filter Logbook")
    
    # Dropdown Pilih Bulan
    list_bulan = df['Bulan'].unique()
    selected_bulan = st.sidebar.selectbox("1. Pilih Bulan Magang", list_bulan)
    
    # Filter data berdasarkan bulan terpilih
    df_bulan = df[df['Bulan'] == selected_bulan]
    
    # Dropdown Pilih Hari/Tanggal
    list_tanggal = df_bulan['date'].unique()
    selected_tanggal = st.sidebar.selectbox("2. Pilih Tanggal", list_tanggal)
    
    # Filter final untuk ditampilkan
    final_df = df_bulan[df_bulan['date'] == selected_tanggal]
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"Ditemukan **{len(final_df)}** pesan pada tanggal ini.")

    # --- MAIN AREA UI ---
    st.subheader(f"Rekap Aktivitas: {selected_tanggal}")
    st.markdown("---")
    
    # Menampilkan UI Bubble Chat
    for index, row in final_df.iterrows():
        # Menentukan apakah ini chat kamu atau dia untuk mengatur avatar UI
        is_user = "Stef" not in row['sender'] # Asumsi selain Stef adalah kamu
        
        with st.chat_message("user" if is_user else "assistant"):
            st.markdown(f"**{row['sender']}** <span style='font-size:0.8em; color:gray;'>• {row['time']}</span>", unsafe_allow_html=True)
            st.write(row['message'])