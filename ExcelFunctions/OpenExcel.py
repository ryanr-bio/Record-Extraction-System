import pandas as pd

def load_in_file(filepath, sheet_name):
    df = pd.read_excel(filepath, sheet_name, engine= "calamine")
    df = df.drop(columns= ['Unnamed: 36', 'Unnamed: 37', 'Unnamed: 38', 
                           'Unnamed: 39', 'Unnamed: 40', 'Unnamed: 41', 
                           'Unnamed: 42', 'Unnamed: 43', 'Unnamed: 44', 
                           'Unnamed: 45', 'Unnamed: 46', 'Unnamed: 47', 
                           'Unnamed: 48', 'Unnamed: 49', 'Unnamed: 50', 
                           'Unnamed: 51', 'Unnamed: 52', 'Unnamed: 53', 
                           'Unnamed: 54', 'Unnamed: 55', 'Unnamed: 56', 
                           'Unnamed: 57', 'Unnamed: 58', 'Unnamed: 59', 
                           'Unnamed: 60'])
    return df

def get_column_names(df):
    df = df.drop(columns= ['s.no', 'Comp ID', 'Gender', 'Age'])
    columns = df.columns.str.strip().str.lower().to_list()
    return columns
