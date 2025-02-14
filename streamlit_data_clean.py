import streamlit as st
import pandas as pd
import numpy as np
import re
from sklearn.preprocessing import LabelEncoder

st.title("Data Cleaning & Preprocessing by NdreasX_")


uploaded_file = st.file_uploader("Upload file CSV atau Excel", type=["csv", "xlsx"])


if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_name = st.selectbox("Pilih sheet yang ingin digunakan", excel_file.sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    
    st.write("### Data Awal:")
    st.dataframe(df)
    
    if "selected_columns" not in st.session_state:
        st.session_state.selected_columns = []
        column_options = ["Semua Kolom"] + df.columns.tolist()
    
    valid_defaults = [col for col in st.session_state.selected_columns if col in column_options]

    selected_columns = st.multiselect(
        "Pilih kolom yang ingin digunakan",
        column_options,
        default=valid_defaults
    )
    
    if "Semua Kolom" in selected_columns:
        if set(st.session_state.selected_columns) != set(df.columns.tolist()):  
            st.session_state.selected_columns = df.columns.tolist()
            st.rerun()
    else:
        st.session_state.selected_columns = selected_columns

    
    if selected_columns:
        df = df[selected_columns]
        
        
        if st.checkbox("Ingin melakukan rename kolom?"):
            rename_dict = {}
            columns_to_rename = st.multiselect("Pilih kolom yang ingin diubah namanya", df.columns.tolist())
            
            for col in columns_to_rename:
                new_name = st.text_input(f"Ubah '{col}' menjadi:", key=f"rename_{col}")
                if new_name:
                    rename_dict[col] = new_name
            
            df.rename(columns=rename_dict, inplace=True)
        
        engine_size_variants = {'engine size', 'engine_size', 'enginesize', 'engine size2', 'engine_size2', 'enginesize2'}
        df.columns = df.columns.str.lower()
        
        matching_column = next((col for col in df.columns if col in engine_size_variants), None)
        if matching_column:
            def convert_to_cc(value):
                try:
                    num = float(value)
                    if num < 10:
                        return int(num * 1000)
                    return int(num)
                except ValueError:
                    return np.nan
            
            df['engine size'] = df[matching_column].apply(convert_to_cc)
            df.drop(columns=[matching_column], inplace=True)
        
        if st.checkbox("Ingin melakukan konversi kolom kategorikal?"):
            categorical_columns = st.multiselect("Pilih kolom kategorikal untuk dikonversi", df.select_dtypes(include=['object']).columns.tolist())
            if categorical_columns:
                le = LabelEncoder()
                for col in categorical_columns:
                    df[col] = le.fit_transform(df[col].astype(str))
        
        if st.checkbox("Ingin membersihkan data numerik?"):
            # Fungsi membersihkan angka dari string
            def clean_numeric(value):
                if isinstance(value, str):
                    value = value.replace(',', '').strip()  # Hilangkan koma dan spasi
                    value = re.sub(r'[^0-9.]', '', value)   # Hilangkan karakter non-numerik

                try:
                    return "{:.0f}".format(float(value))
                except (ValueError, TypeError):
                    return ""
                except Exception:
                    return value
            
            def clean_date(value):
                try:
                    return pd.to_datetime(value, errors="coerce").strftime("%d-%m-%Y")
                except Exception:
                    return np.nan
            
            numeric_columns = st.multiselect(
                "Pilih kolom yang ingin dibersihkan sebagai numerik", 
                df.select_dtypes(exclude=['object']).columns.tolist()
            )
            for col in numeric_columns:
                df[col] = df[col].apply(clean_numeric)

            if st.checkbox("Ingin mengoreksi data tanggal?"):
                date_columns = st.multiselect(
                    "Pilih kolom yang ingin dikonversi ke format tanggal (DD-MM-YYYY)",
                    df.columns.tolist()
                )
                for col in date_columns:
                    df[col] = df[col].apply(clean_date)
            
            if st.checkbox("Ingin membersihkan teks dari duplikasi?"):
                def clean_text(value):
                    if isinstance(value, str):
                        words = [word.strip() for word in value.split(";") if word.strip()]
                        unique_words = list(dict.fromkeys(words))
                        return "; ".join(unique_words)
                    return value
                
                text_columns = st.multiselect(
                    "Pilih kolom teks yang ingin dibersihkan",
                    df.select_dtypes(include=['object']).columns.tolist()
                )
                for col in text_columns:
                    df[col] = df[col].apply(clean_text)
        
        if st.checkbox("Hapus missing values"):
            df.dropna(inplace=True)
        
        if st.checkbox("Ingin menukar value antara dua kolom?"):
            row_index = st.number_input("Masukkan nomor baris untuk ditukar (index mulai dari 0)", min_value=0, max_value=len(df)-1, step=1)
            
            col1, col2 = st.selectbox("Pilih kolom pertama", df.columns.tolist(), key="swap_col1"), \
                        st.selectbox("Pilih kolom kedua", df.columns.tolist(), key="swap_col2")
            
            if st.button("Tukar value"):
                if col1 in df.columns and col2 in df.columns:
                    df.at[row_index, col1], df.at[row_index, col2] = df.at[row_index, col2], df.at[row_index, col1]
                    st.success(f"Berhasil menukar value pada baris {row_index} dari kolom '{col1}' ke '{col2}'!")
                    st.write("### Data Setelah Pertukaran:")
                    st.dataframe(df)
                else:
                    st.error("Kolom yang dipilih tidak valid.")
        
        if st.checkbox("Ingin memindahkan kolom?", key="move_checkbox"):
            col1 = st.selectbox("Pilih kolom yang ingin dipindahkan", df.columns.tolist(), key="move_col1")
            col2 = st.selectbox("Pilih kolom referensi", df.columns.tolist(), key="move_col2")
            direction = st.selectbox("Pilih arah", ["Kanan", "Kiri"], key="move_direction")

            if col1 == col2:
                st.error("Kolom yang dipilih tidak boleh sama.")
            elif col1 not in df.columns or col2 not in df.columns:
                st.error("Kolom yang dipilih tidak valid.")
            else:
                if direction == "Kanan":
                    cols = df.columns.tolist()
                    cols.insert(cols.index(col2), cols.pop(cols.index(col1)))
                elif direction == "Kiri":
                    cols = df.columns.tolist()
                    cols.insert(cols.index(col2), cols.pop(cols.index(col1)))
                df = df[cols]
                st.success(f"Berhasil memindahkan kolom '{col1}' ke {direction.lower()} dari kolom '{col2}'!")
                # st.write("### Data Setelah Pemindahan:")
                # st.write(df.head())
             
        if st.checkbox("Replace Value"):
            replace_column = st.multiselect("Pilih kolom yang ingin diubah nilainya", df.columns.tolist())
            
            if replace_column:
                replace_dict = {}
                for col in replace_column:
                    unique_values = df[col].unique()
                    for value in unique_values:
                        new_value = st.text_input(f"Ubah '{value}' pada '{col.upper()}' menjadi:", key=f"replace_{col}_{value}")
                        if new_value:
                            replace_dict[value] = new_value.lower()
                    df[col] = df[col].replace(replace_dict)
        
                
        target_addreas = ['address', 'alamat']
        df.columns = df.columns.str.lower()
        target_column = next((col for col in df.columns if col in target_addreas), None)

        if st.checkbox("Ingin membersihkan kolom alamat?"):
            def clean_address(value):
                if pd.isna(value) or pd.isnull(value):
                    return value
                if isinstance(value, str):
                    value = value.strip()
                    if len(value) <= 1 or len(value) < 3:
                        return ""
                    return value.strip()
                return value
            df[target_column] = df[target_column].apply(clean_address)
            
        
        selected_columns = df.columns.tolist()
        st.write("### Data Setelah Preprocessing:")
        st.dataframe(df)
        

        if st.checkbox("Cek Unique Values"):
            check_unique_column = st.selectbox("Pilih kolom untuk melihat Unique Values", selected_columns)
            if check_unique_column:
                unique_values = df[check_unique_column].unique()
                Total_Uniques = len(unique_values)
                st.write(f"Total Uniques: {Total_Uniques}")
                st.write(f"### Unique Values dari kolom '{check_unique_column}':")
                st.write(unique_values)

        if st.checkbox("Group By"):
            group_by_column = st.selectbox("Pilih kolom untuk Group By", df.columns.tolist())

            if group_by_column:
                grouped_data = {name: pd.DataFrame(group) for name, group in df.groupby(group_by_column)} # Dictionary untuk Group By pertama
                unique_values = df[group_by_column].dropna().unique()

                second_grouped_data = {} # Dictionary untuk Group By kedua

                st.write(f"### Data Grouped by {group_by_column}:")
                for value in unique_values:
                    if value in grouped_data:
                        st.write(f"#### {group_by_column}: {value}")
                        st.dataframe(grouped_data[value])

                        add_second_group_by = st.checkbox(f"Tambahkan Group By kedua untuk '{value}'?", key=f"group2_{value}")

                        if add_second_group_by:
                            second_group_by_column = st.selectbox(
                                f"Pilih kolom kedua untuk Group By pada {value}", 
                                df.columns.tolist(), 
                                key=f"second_group_{value}"
                            )

                            if second_group_by_column:
                                second_grouped_data[value] = {
                                    f"{value} ~ {second_value}": pd.DataFrame(group) 
                                    for second_value, group in grouped_data[value].groupby(second_group_by_column)
                                }

                                st.write(f"### Data Grouped by {second_group_by_column} within {value}:")
                                for second_key, data in second_grouped_data[value].items():
                                    st.write(f"##### {second_key}")
                                    st.dataframe(data)

            if grouped_data or second_grouped_data:
                def download_excel_file(output_file, groupby_choice, grouped_data, second_grouped_data):
                    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
                        df.to_excel(writer, sheet_name="Complete Data", index=False)

                        if groupby_choice == "Group By 1":
                            for key, data in grouped_data.items():
                                data.to_excel(writer, sheet_name=str(key), index=False)
                        else:
                            for group1, group2_dict in second_grouped_data.items():
                                for key, data in group2_dict.items():
                                    data.to_excel(writer, sheet_name=key[:31], index=False)

                    with open(output_file, "rb") as file:
                        st.success(f"File {output_file} berhasil didownload!")
                
                if second_grouped_data:
                    for value, data_dict in second_grouped_data.items():
                        st.write(f"### Data Grouped by {second_group_by_column} within {value}:")
                        for second_key, data in data_dict.items():
                            st.write(f"##### {second_key}")
                            st.dataframe(data)

                if st.checkbox("Download hasil Group By sebagai file Excel?"):
                    output_file_name = st.text_input("Masukkan nama file output (tanpa ekstensi)", value="cleaned_data")
                    groupby_choice = st.radio("Pilih hasil Group By yang ingin didownload", ("Group By 1", "Group By 2"))

                    if st.button("Download Excel"):
                        output_file = f"{output_file_name}.xlsx"
                        download_excel_file(output_file, groupby_choice, grouped_data, second_grouped_data)
