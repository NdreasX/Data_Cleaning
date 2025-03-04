import streamlit as st
st.set_page_config(page_title="Gabung & Validasi Data", layout="wide", initial_sidebar_state="expanded")

import pandas as pd
import re
import io

# ---------------------------
# Custom CSS untuk Styling UI
# ---------------------------
st.markdown("""
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .header-section {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------
# Fungsi Utility
# ---------------------------
def clean_column_name(name):
    """Bersihkan nama kolom dengan menghilangkan karakter non-alfanumerik dan mengubah ke huruf kecil."""
    return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

@st.cache_data(show_spinner=False)
def load_csv(file):
    return pd.read_csv(file)

@st.cache_data(show_spinner=False)
def load_excel(file, sheet):
    return pd.read_excel(file, sheet_name=sheet)

# ---------------------------
# Mode Operasi: Validasi Saja
# ---------------------------
def validasi_saja(df1, df2, pk1, pk2, cmp1, cmp2):
    results = []
    for _, row1 in df1.iterrows():
        key_val = row1[pk1]
        val1 = row1[cmp1]
        matching = df2[df2[pk2] == key_val]
        if not matching.empty:
            val2 = matching.iloc[0][cmp2]
            status = "Valid" if val1 == val2 else "Tidak Valid"
        else:
            val2 = None
            status = "Tidak Ada pada Data 2"
        row_result = row1.to_dict()
        row_result[f"{cmp1}_Data1"] = val1
        row_result[f"{cmp2}_Data2"] = val2
        row_result["Status"] = status
        results.append(row_result)
    return pd.DataFrame(results)

# ---------------------------
# Mode Operasi: Gabung & Validasi
# ---------------------------
def gabung_validasi_data(df1, df2, pk1, pk2, cmp1, cmp2):
    results = []
    # Proses validasi untuk Data 1
    for _, row1 in df1.iterrows():
        key_val = row1[pk1]
        val1 = row1[cmp1]
        matching = df2[df2[pk2] == key_val]
        if not matching.empty:
            val2 = matching.iloc[0][cmp2]
            status = "Valid" if val1 == val2 else "Tidak Valid"
        else:
            val2 = None
            status = "Tidak Ada pada Data 2"
        row_result = row1.to_dict()
        row_result[f"{cmp1}_Data1"] = val1
        row_result[f"{cmp2}_Data2"] = val2
        row_result["Status"] = status
        results.append(row_result)
        
    # Proses untuk data di Data 2 yang tidak ada di Data 1
    pk1_values = set(df1[pk1])
    missing_rows = df2[~df2[pk2].isin(pk1_values)]
    if not missing_rows.empty:
        st.info("Data dari Data 2 yang tidak ditemukan di Data 1:")
        st.dataframe(missing_rows.head(), height=150)
        auto_merge = st.checkbox("Otomatis gabungkan kolom dengan nama sama dari Data 2", value=True, key="auto_merge")
        if auto_merge:
            clean_cols_df1 = {clean_column_name(col): col for col in df1.columns}
            clean_cols_df2 = {clean_column_name(col): col for col in df2.columns}
            selected_columns = [clean_cols_df2[col] for col in clean_cols_df2 if col in clean_cols_df1]
        else:
            selected_columns = st.multiselect("Pilih kolom dari Data 2 untuk ditambahkan", 
                                              df2.columns.tolist(), default=[pk2], key="selected_cols")
        for _, row2 in missing_rows.iterrows():
            key_val = row2[pk2]
            new_row = {col: None for col in df1.columns}
            new_row[pk1] = key_val
            for col in selected_columns:
                col_clean = clean_column_name(col)
                clean_cols_df1 = {clean_column_name(c): c for c in df1.columns}
                if col_clean in clean_cols_df1:
                    target_col = clean_cols_df1[col_clean]
                    new_row[target_col] = row2[col]
            new_row[f"{cmp1}_Data1"] = None
            new_row[f"{cmp2}_Data2"] = row2[cmp2]
            new_row["Status"] = "Tidak Ada pada Data 1"
            results.append(new_row)
    return pd.DataFrame(results)

# ---------------------------
# Mode Operasi: Gabung Data Saja
# ---------------------------
def gabung_data_saja(df1, df2, pk1, pk2):
    # Lakukan full outer join berdasarkan primary key
    merged_df = pd.merge(df1, df2, how="outer", left_on=pk1, right_on=pk2, suffixes=("_Data1", "_Data2"))
    
    # Penggabungan kolom: untuk kolom yang sama di kedua data (selain primary key)
    # Buat mapping nama kolom yang telah dibersihkan untuk masing-masing dataframe
    norm_df1 = {clean_column_name(col): col for col in df1.columns if col != pk1}
    norm_df2 = {clean_column_name(col): col for col in df2.columns if col != pk2}
    
    # Cari kolom umum berdasarkan nama yang telah dinormalisasi
    common_norm = set(norm_df1.keys()).intersection(set(norm_df2.keys()))
    
    for norm in common_norm:
        col1 = norm_df1[norm] + "_Data1"  # kolom dari df1 setelah merge
        col2 = norm_df2[norm] + "_Data2"  # kolom dari df2 setelah merge
        if col1 in merged_df.columns and col2 in merged_df.columns:
            # Gabungkan dengan prioritas nilai dari Data1 jika tidak null
            merged_df[norm_df1[norm]] = merged_df[col1].combine_first(merged_df[col2])
            # Hapus kolom yang terpisah karena sudah digabungkan
            merged_df = merged_df.drop(columns=[col1, col2])
    
    # Jangan menghilangkan kolom primary key, sehingga baik pk1 maupun pk2 (jika ada) tetap tampil
    return merged_df


# ---------------------------
# Sidebar: Unggah Data
# ---------------------------
st.sidebar.header("Langkah 1: Unggah Data")
file1 = st.sidebar.file_uploader("Unggah File Data 1 (CSV/Excel)", type=["csv", "xlsx"], key="file1")
file2 = st.sidebar.file_uploader("Unggah File Data 2 (CSV/Excel)", type=["csv", "xlsx"], key="file2")

df1, df2 = None, None
if file1:
    if file1.name.endswith(".xlsx"):
        sheets1 = pd.ExcelFile(file1).sheet_names
        sheet1 = st.sidebar.selectbox("Pilih Sheet untuk Data 1", sheets1, key="sheet1")
        df1 = load_excel(file1, sheet1)
    else:
        df1 = load_csv(file1)
    st.sidebar.success("Data 1 berhasil diunggah.")
    st.subheader("Preview Data 1")
    st.dataframe(df1.head(), height=150)
    
if file2:
    if file2.name.endswith(".xlsx"):
        sheets2 = pd.ExcelFile(file2).sheet_names
        sheet2 = st.sidebar.selectbox("Pilih Sheet untuk Data 2", sheets2, key="sheet2")
        df2 = load_excel(file2, sheet2)
    else:
        df2 = load_csv(file2)
    st.sidebar.success("Data 2 berhasil diunggah.")
    st.subheader("Preview Data 2")
    st.dataframe(df2.head(), height=150)

# ---------------------------
# Sidebar: Konfigurasi & Pilih Mode Operasi
# ---------------------------
if df1 is not None and df2 is not None:
    st.sidebar.header("Langkah 2: Konfigurasi Data")
    mode = st.sidebar.radio("Pilih Mode Operasi", ["Gabung & Validasi", "Validasi Saja", "Gabung Data Saja"])
    pk1 = st.sidebar.selectbox("Pilih Primary Key dari Data 1", df1.columns, key="pk1")
    pk2 = st.sidebar.selectbox("Pilih Primary Key dari Data 2", df2.columns, key="pk2")
    
    if mode in ["Gabung & Validasi", "Validasi Saja"]:
        cmp1 = st.sidebar.selectbox("Pilih Kolom Validasi dari Data 1", df1.columns, key="cmp1")
        cmp2 = st.sidebar.selectbox("Pilih Kolom Validasi dari Data 2", df2.columns, key="cmp2")
    
    with st.expander("Instruksi Proses Operasi", expanded=True):
        st.markdown(
            """
            **Panduan:**
            1. **Upload Data:** Unggah kedua file data (CSV atau Excel).
            2. **Konfigurasi:** Pilih primary key (dan kolom validasi jika diperlukan).
            3. **Operasi:** Pilih mode operasi:
                - **Gabung & Validasi:** Validasi data dan gabungkan data yang hanya ada di Data 2.
                - **Validasi Saja:** Hanya validasi data.
                - **Gabung Data Saja:** Gabungkan kedua data dan gabungkan kolom dengan nama sama.
            4. **Hasil & Unduh:** Lihat hasil operasi dan unduh sebagai Excel jika diinginkan.
            """
        )
    
    # ---------------------------
    # Proses Operasi Berdasarkan Mode
    # ---------------------------
    st.header("Langkah 3: Hasil Operasi")
    if mode == "Validasi Saja":
        result_df = validasi_saja(df1, df2, pk1, pk2, cmp1, cmp2)
    elif mode == "Gabung & Validasi":
        result_df = gabung_validasi_data(df1, df2, pk1, pk2, cmp1, cmp2)
    elif mode == "Gabung Data Saja":
        result_df = gabung_data_saja(df1, df2, pk1, pk2)
    
    # Atur urutan kolom untuk mode validasi
    if mode in ["Validasi Saja", "Gabung & Validasi"]:
        base_cols = list(df1.columns)
        if cmp1 in base_cols:
            insert_index = base_cols.index(cmp1) + 1
            base_cols.insert(insert_index, f"{cmp1}_Data1")
            base_cols.insert(insert_index + 1, f"{cmp2}_Data2")
            base_cols.insert(insert_index + 2, "Status")
        if cmp1 in base_cols:
            base_cols.remove(cmp1)
        final_cols = [col for col in base_cols if col in result_df.columns]
    else:
        final_cols = result_df.columns.tolist()
    
    if mode in ["Validasi Saja", "Gabung & Validasi"]:
        selected_status = st.multiselect("Pilih status yang ingin ditampilkan", 
                                         ['Valid', 'Tidak Valid', 'Tidak Ada pada Data 2', 'Tidak Ada pada Data 1'],
                                         default=['Valid', 'Tidak Valid', 'Tidak Ada pada Data 2', 'Tidak Ada pada Data 1'])
        if selected_status:
            result_df = result_df[result_df["Status"].isin(selected_status)]
        else:
            st.warning("Pilih setidaknya satu status untuk ditampilkan.")
    
    st.subheader(f"Hasil Operasi ({mode})")
    st.dataframe(result_df[final_cols], height=300)
    
    # ---------------------------
    # Unduh Hasil
    # ---------------------------
    st.header("Langkah 4: Unduh Hasil")
    if st.checkbox("Unduh hasil sebagai file Excel?"):
        output_file_name = st.text_input("Masukkan nama file output (tanpa ekstensi)")
        if st.button("Download Excel"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                result_df[final_cols].to_excel(writer, index=False)
            output.seek(0)
            st.download_button(
                label="Download Excel",
                data=output,
                file_name=f"{output_file_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
