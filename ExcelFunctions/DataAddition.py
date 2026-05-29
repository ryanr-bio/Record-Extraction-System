# from openpyxl import load_workbook
import pandas as pd

def specific_id_row(dataframe, specific_id):
    rows = dataframe.loc[dataframe['Comp ID']==int(specific_id)]
    return rows

def row_num_checker(rows, total_records):
    total_extract = len(total_records)
    if len(rows)==total_extract:
            flag = 0
    elif len(rows)>total_extract:
            flag = 0
    else:
        flag = total_extract - len(rows)
    return flag

def check_row_data(rows):
    columns = ['Primary ICD', 'Nationality', 'Chief Complaint']
    indices = []
    for i in rows.index:
        row = rows.loc[i]
        if any(str(row.get(col)) == 'nan' for col in columns):
            indices.append(int(i))
    return indices
    
def data_per_row(df, records, comp_id):
    dates = df.loc[df['Comp ID'] == int(comp_id), 'Visit Date']
    proper_dates = pd.to_datetime(dates, 
                                  errors='coerce', 
                                  dayfirst= True).dt.strftime("%d-%m-%Y").tolist()
    data = dict()
    errors = []
    for key,value in records.items():
        if key == 'Unknown':
            data[key] = value
            continue
        parsed_key = pd.to_datetime(key, errors='coerce', dayfirst=True)
        if pd.isna(parsed_key):
            errors.append(f"Comp ID: {comp_id} | Date key: {key}\n")
            continue
        proper_key = parsed_key.strftime("%d-%m-%Y")
        if not proper_key in proper_dates:
            data[key] = value
    if errors:
        print(f'''Errors found for Comp ID {comp_id}. 
              Check data_errors.txt for details.''')
        with open("data_errors.txt", "a") as f:
            f.writelines(errors)
    data = dict(sorted(
        data.items(),
        key=lambda item: pd.to_datetime(item[0], errors='coerce', dayfirst=True)
        if item[0] != 'Unknown' else pd.Timestamp.max
    ))
    return data

def add_data_to_excel(data, ws, starting_column, row_num, initial_data=None):
    for i, value in enumerate(data):
        if initial_data:
            for j, initial_value in enumerate(initial_data, start= 1):
                ws.cell(row=int(row_num) + 2, column= j, value=initial_value)
        ws.cell(row=int(row_num) + 2, column=starting_column + i, value=value)

    print(f"Added data to row {row_num + 2}")
    return True