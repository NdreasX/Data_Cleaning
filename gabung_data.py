import streamlit as st
import pandas as pd
import re
import io

st.title('Gabung & Validasi Data')

def bersihkan_nama_kolom(nama):
    return re.sub(r'[^a-zA-Z0-9]', '', nama).lower()

file1 = st.file_uploader("Upload File Data 1 (CSV atau Excel)", type=["csv", "xlsx"])
if file1:
    if file1.name.endswith(".xlsx"):
        sheet1 = pd.ExcelFile(file1).sheet_names
        sheet1_selected = st.selectbox("Pilih Sheet untuk Data 1", sheet1)
        df1 = pd.read_excel(file1, sheet_name=sheet1_selected)
    else:
        df1 = pd.read_csv(file1)

    st.write("Data 1:")
    st.write(df1.head())

file2 = st.file_uploader("Upload File Data 2 (CSV atau Excel)", type=["csv", "xlsx"])
if file2:
    if file2.name.endswith(".xlsx"):
        sheet2 = pd.ExcelFile(file2).sheet_names
        sheet2_selected = st.selectbox("Pilih Sheet untuk Data 2", sheet2)
        df2 = pd.read_excel(file2, sheet_name=sheet2_selected)
    else:
        df2 = pd.read_csv(file2)

    st.write("Data 2:")
    st.write(df2.head())

if file1 and file2:
    primary_key_1 = st.selectbox("Pilih Kolom Primary Key dari Data 1", df1.columns)
    primary_key_2 = st.selectbox("Pilih Kolom Primary Key dari Data 2", df2.columns)

    compare_col_1 = st.selectbox("Pilih Kolom Validasi dari Data 1", df1.columns)
    compare_col_2 = st.selectbox("Pilih Kolom Validasi dari Data 2", df2.columns)

    hasil_validasi = []

    kolom_bersih_1 = {bersihkan_nama_kolom(col): col for col in df1.columns}
    kolom_bersih_2 = {bersihkan_nama_kolom(col): col for col in df2.columns}

    for _, row1 in df1.iterrows():
        pk1 = row1[primary_key_1]
        val1 = row1[compare_col_1]

        row2 = df2[df2[primary_key_2] == pk1]

        if not row2.empty:
            val2 = row2.iloc[0][compare_col_2]
            status = "Valid" if val1 == val2 else "Tidak Valid"
        else:
            val2 = None
            status = "Tidak Ada pada Data 2"

        row_hasil = row1.to_dict()
        row_hasil[f"{compare_col_1}_Data1"] = val1
        row_hasil[f"{compare_col_2}_Data2"] = val2
        row_hasil["Status"] = status

        hasil_validasi.append(row_hasil)

    pk1_values = set(df1[primary_key_1])
    pk2_tidak_ada_di_pk1 = []

    for _, row2 in df2.iterrows():
        pk2 = row2[primary_key_2]

        if pk2 not in pk1_values:
            pk2_tidak_ada_di_pk1.append(row2)

    if pk2_tidak_ada_di_pk1:
        st.write("Ada data di Data 2 yang Primary Key-nya tidak ditemukan di Data 1.")
        st.write(pd.DataFrame(pk2_tidak_ada_di_pk1))

        cek_otomatis = st.checkbox("Otomatis Gabungkan Kolom dengan Nama Sama dari Data 2")

        if cek_otomatis:
            kolom_diambil_dari_data2 = [kolom_bersih_2[col] for col in kolom_bersih_2 if col in kolom_bersih_1]
        else:
            kolom_diambil_dari_data2 = st.multiselect(
                "Pilih Kolom dari Data 2 untuk Ditambahkan ke Hasil",
                df2.columns.tolist(),
                default=[kolom_bersih_2.get(primary_key_2, primary_key_2)]
            )

        for row2 in pk2_tidak_ada_di_pk1:
            pk2 = row2[primary_key_2]

            row_hasil = {col: None for col in df1.columns}
            row_hasil[primary_key_1] = pk2

            for kolom in kolom_diambil_dari_data2:
                kolom_bersih = bersihkan_nama_kolom(kolom)
                if kolom_bersih in kolom_bersih_1:
                    kolom_target = kolom_bersih_1[kolom_bersih]
                    row_hasil[kolom_target] = row2[kolom]

            row_hasil[f"{compare_col_1}_Data1"] = None
            row_hasil[f"{compare_col_2}_Data2"] = row2[compare_col_2]
            row_hasil["Status"] = "Tidak Ada pada Data 1"

            hasil_validasi.append(row_hasil)

    hasil_df = pd.DataFrame(hasil_validasi)

    kolom_awal = list(df1.columns)
    if compare_col_1 in kolom_awal:
        idx_valid1 = kolom_awal.index(compare_col_1) + 1
        kolom_awal.insert(idx_valid1, f"{compare_col_1}_Data1")
        kolom_awal.insert(idx_valid1 + 1, f"{compare_col_2}_Data2")
        kolom_awal.insert(idx_valid1 + 2, "Status")

    kolom_awal.remove(compare_col_1)
    kolom_akhir = [kol for kol in kolom_awal if kol in hasil_df.columns]
    show_status = st.multiselect('pilih status yang ingin ditampilkan', ['Tidak Valid', 'Valid', 'Tidak Ada pada Data 2', 'Tidak Ada pada Data 1'])
    
    if show_status:
        hasil_df_filtered = hasil_df[hasil_df["Status"].isin(show_status)]
        st.write(f"Hasil Validasi ({show_status}):")
        st.dataframe(hasil_df_filtered[kolom_akhir])
    
    if st.checkbox("Unduh hasil validasi sebagai file Excel?"):
        output_file_name = st.text_input("Masukkan nama file output (tanpa ekstensi)", value="hasil_validasi")
        if st.button("Download Excel"):
            output_file = io.BytesIO()
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                hasil_df_filtered[kolom_akhir].to_excel(writer, index=False)
            output_file.seek(0)
    
            st.download_button(
                label="Download Excel",
                data=output_file,
                file_name=f"{output_file_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
