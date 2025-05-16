# app.py (Kode 2 - Final + Debug Info)
import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import BytesIO

st.set_page_config(page_title="Aplikasi Kode 2 - Naik Turun Golongan", layout="centered")
st.title("Rekap Nominal Naik Turun Golongan")

# Pilih rentang tanggal (aktifkan mode rentang)
date_range = st.date_input(
    "Pilih rentang tanggal (filter)",
    value=(date(2025, 5, 5), date(2025, 5, 13))
)

# Upload input files
uploaded_tsum = st.file_uploader("Upload file Excel Tiket Summary", type=["xlsx"], key="tsum")
uploaded_inv = st.file_uploader("Upload file Excel Invoice", type=["xlsx"], key="inv")

if uploaded_tsum and uploaded_inv and isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    end_date = end_date + pd.Timedelta(hours=23, minutes=59, seconds=59)

    # Baca file
    df_tsum = pd.read_excel(uploaded_tsum)
    df_inv = pd.read_excel(uploaded_inv)

    df_tsum['PEMESANAN'] = pd.to_datetime(df_tsum['PEMESANAN'], errors='coerce')
    df_inv['TANGGAL INVOICE'] = pd.to_datetime(df_inv['TANGGAL INVOICE'], errors='coerce')

    # Debug: tampilkan jumlah baris awal
    st.write("Jumlah baris TSUM sebelum filter:", len(df_tsum))
    st.write("Jumlah baris INV sebelum filter:", len(df_inv))

    # Filter tanggal
    df_tsum_filtered = df_tsum[(df_tsum['PEMESANAN'] >= start_date) & (df_tsum['PEMESANAN'] <= end_date)]
    df_inv_filtered = df_inv[(df_inv['TANGGAL INVOICE'] >= start_date) & (df_inv['TANGGAL INVOICE'] <= end_date)]

    # Debug: tampilkan jumlah baris hasil filter
    st.write("Jumlah baris TSUM setelah filter:", len(df_tsum_filtered))
    st.write("Jumlah baris INV setelah filter:", len(df_inv_filtered))

    if df_tsum_filtered.empty and df_inv_filtered.empty:
        st.warning("Tidak ditemukan data dalam rentang tanggal tersebut.")
    else:
        # Siapkan baris TSUM untuk digabungkan
        tsum_rows = pd.DataFrame({
            'NOMER INVOICE': df_tsum_filtered['NOMOR INVOICE'],
            'HARGA': -df_tsum_filtered['TARIF'],
            'KEBERANGKATAN': df_tsum_filtered['ASAL'].astype(str).str.strip().str.upper()
        })

        # Siapkan INV dan normalisasi
        inv_rows = df_inv_filtered[['NOMER INVOICE', 'HARGA', 'KEBERANGKATAN']].copy()
        inv_rows['KEBERANGKATAN'] = inv_rows['KEBERANGKATAN'].astype(str).str.strip().str.upper()

        # Gabungkan dan hitung selisih
        combined = pd.concat([inv_rows, tsum_rows], ignore_index=True)
        result = combined.groupby('KEBERANGKATAN')['HARGA'].sum().reset_index()
        result = result.rename(columns={'KEBERANGKATAN': 'ASAL', 'HARGA': 'Nominal Naik Turun Golongan'})
        result['Nominal Naik Turun Golongan'] = result['Nominal Naik Turun Golongan'].astype(int)

        # Tambah baris kosong dan total
        blank_row = pd.DataFrame([{'ASAL': '', 'Nominal Naik Turun Golongan': ''}])
        total_sum = result['Nominal Naik Turun Golongan'].sum()
        total_row = pd.DataFrame([{'ASAL': 'Total', 'Nominal Naik Turun Golongan': total_sum}])
        result_with_total = pd.concat([result, blank_row, total_row], ignore_index=True)

        # Tampilkan tabel
        result_display = result_with_total.copy()
        result_display['Nominal Naik Turun Golongan'] = result_display['Nominal Naik Turun Golongan'].apply(
            lambda x: f"{int(x):,}".replace(",", ".") if isinstance(x, int) else x
        )

        st.subheader("Hasil Rekap")
        st.table(result_display)

        # Tombol download Excel
        output = BytesIO()
        result_with_total.to_excel(output, index=False, engine='openpyxl')
        st.download_button(
            label="Download Hasil ke Excel",
            data=output.getvalue(),
            file_name="naik_turun_golongan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Silakan upload kedua file Excel dan pilih rentang tanggal untuk memulai perhitungan.")
