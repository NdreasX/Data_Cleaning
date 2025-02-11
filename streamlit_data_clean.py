import streamlit as st
import pandas as pd
import numpy as np
import re
from sklearn.preprocessing import LabelEncoder

st.title("Data Cleaning & Preprocessing dengan Streamlit")


uploaded_file = st.file_uploader("Upload file CSV atau Excel", type=["csv", "xlsx"])

def clean_numeric(value):
    if isinstance(value, str):
        value = value.replace(',', '').strip()
        value = re.sub(r'[^0-9.]', '', value)
    
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return np.nan


if uploaded_file is not None:
    # Baca file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.write("### Data Awal:")
    st.dataframe(df)
    
    selected_columns = st.multiselect("Pilih kolom yang ingin digunakan", df.columns.tolist())
    if selected_columns:
        df = df[selected_columns]
        
        # Opsi rename kolom
        if st.checkbox("Ingin melakukan rename kolom?"):
            rename_dict = {}
            columns_to_rename = st.multiselect("Pilih kolom yang ingin diubah namanya", df.columns.tolist())
            
            for col in columns_to_rename:
                new_name = st.text_input(f"Ubah '{col}' menjadi:", key=f"rename_{col}")
                if new_name:
                    rename_dict[col] = new_name
            
            df.rename(columns=rename_dict, inplace=True)
        
        
        if 'engine size' in df.columns:
            def convert_to_cc(value):
                try:
                    num = float(value)
                    if num < 10:
                        return int(num * 1000)
                    return int(num)
                except ValueError:
                    return np.nan
            df['engine size'] = df['engine size'].apply(convert_to_cc)
        
        
        categorical_columns = st.multiselect("Pilih kolom kategorikal untuk dikonversi", df.select_dtypes(include=['object']).columns.tolist())
        if categorical_columns:
            le = LabelEncoder()
            for col in categorical_columns:
                df[col] = le.fit_transform(df[col].astype(str))
        
        
        numeric_columns = st.multiselect("Pilih kolom yang ingin dibersihkan sebagai angka", df.columns.tolist())
        for col in numeric_columns:
            df[col] = df[col].apply(clean_numeric)
        
        
        if st.checkbox("Hapus missing values"):
            df.dropna(inplace=True)
        
        if st.checkbox("Ingin menukar value antar kolom?"):
            row_index = st.number_input("Masukkan index baris untuk ditukar (index mulai dari 0)", min_value=0, max_value=len(df)-1, step=1)
            
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

        
        st.write("### Data Setelah Preprocessing:")
        st.dataframe(df)
        
        
        if not df.empty:
            group_by_column = st.selectbox("Pilih kolom untuk Group By", df.columns.tolist())
            if group_by_column:
                grouped_data = {name: pd.DataFrame(group) for name, group in df.groupby(group_by_column)}
                unique_values = df[group_by_column].dropna().unique()
                
                st.write(f"### Data Grouped by {group_by_column}:")
                for value in unique_values:
                    if value in grouped_data:
                        st.write(f"#### {group_by_column}: {value}")
                        st.dataframe(grouped_data[value])
                        
                        # Pilih kolom untuk Group By kedua
                        second_group_by_column = st.selectbox(f"Pilih kolom kedua untuk Group By pada {value}", df.columns.tolist(), key=value)
                        if second_group_by_column:
                            second_grouped_data = {name: pd.DataFrame(group) for name, group in grouped_data[value].groupby(second_group_by_column)}
                            second_unique_values = grouped_data[value][second_group_by_column].dropna().unique()
                            
                            st.write(f"### Data Grouped by {second_group_by_column} within {value}:")
                            for second_value in second_unique_values:
                                if second_value in second_grouped_data:
                                    st.write(f"#### {value} {second_group_by_column}: {second_value}")
                                    st.dataframe(second_grouped_data[second_value])
