import time
start_time = time.perf_counter()
import os, tempfile
from openpyxl import load_workbook
from llama_cpp import Llama
from concurrent.futures import ThreadPoolExecutor
from LLMFunctions.LlamaResponse import llm_response
from DriveFunctions.Google import Create_Service
from DriveFunctions.FolderDive import get_ParentFolderId, Search_Folder, Search_Folder_with_names
from DriveFunctions.GetImages import get_image_bytes
from OCRFunctions.TextRecognition import Text_from_images, Record_Grouping_with_Dates, new_edit_image
from OCRFunctions.OCRCleaner import master_clean_ocr, remove_sidebar_noise
from OCRFunctions.ICDManual import find_primary_icd
from ExcelFunctions.OpenExcel import load_in_file, get_column_names
from ExcelFunctions.DataAddition import specific_id_row, row_num_checker, check_row_data, data_per_row, add_data_to_excel
from JSONExtract.JSONtoPy import extract_json, age_checker, extract_last_datetime, pick_later_time
from JSONExtract.CheckPointSystem import check_progress, save_progress
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
from paddleocr import PaddleOCR
import paddle

CLIENT_FILE = 'credentials.json'
API_NAME = 'drive'
API_VER = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

filepath = r"g:\ER Visits(Above 60) - Jan 2020 to Jun 2025 - Copy.xlsx"

sheet_name= "Visit Recs"

file = load_in_file(filepath= filepath, sheet_name= sheet_name)

column_names = get_column_names(file)

wb = load_workbook(filename= filepath)
ws = wb[sheet_name]

checkpointfile = "checkpoint.json"

system_content = '''You are a strict medical data extractor. Extract only 
                  what is explicitly present in the text. Never invent or 
                  infer data. If a field is not found, use null.
                  Always return valid complete JSON. Never use triple quotes.
                  Never leave strings unterminated. Always close all brackets and braces.'''

prompt = '''### GLOBAL RULES:
- Extract from the FIRST occurrence of each field unless stated otherwise.
- Extract only the text directly after the label, stopping at the next section heading or any text ending in ":".
- Do NOT include the label itself in the extracted value.
- Do NOT wrap values in curly braces or any other characters — return plain values only.
- If a field is not found, is empty, or is non-meaningful, return null.

### EXTRACTION RULES:
1. **primary_icd:** You will be given the primary ICD code directly. Find its description from the "Provisional Diagnosis" table and return as "Code - Description".
2. **other_icd:** From the "Provisional Diagnosis" table, list all ICD codes that do NOT have "Yes" after them. Return ONLY raw ICD codes as a comma-separated list. Do NOT include descriptions, disease names, or the primary ICD code.
   - Correct: "J18.9, I10, E11.9"
   - Wrong: "J18.9 - Pneumonia, I10 - Hypertension"
   Include ALL qualifying codes, do not skip any.
3. **chief_complaint:** Find "Chief Complaint & History of Present Illness" or "Chief Complaint and History of Present Illness". Extract only the text after "Triage Category: X" under that heading. Stop before "Past History" or any other section heading.
4. **date_of_birth:** Find "DOB | Age | Gender:". Extract the value before the first vertical bar (|), formatted as DD/MM/YYYY.
5. **nationality:** Value after "Nationality:".
6. **Vitals:** 6. **Vitals:** Find the FIRST occurrence of the "Vitals" subheading only. Stop reading vitals data as soon as you encounter "Vital Reassessment", "Reassessment", "Re-assessment", or any repeated "Vitals" heading. Do NOT mix values from different vitals sections. Find the first row of values under the labels "Temperature", "Pulse", "Respiratory", "BP", "O2SAT". 
    These labels and their values may appear on separate lines.
   - **bp_mmhg:** Find the value under the "BP" label. It MUST contain a forward slash (e.g. "120/80"). If the value does not contain a "/", return null. Strip "mm/Hg". Never return a standalone number as BP.   
   - **temperature_celsius:** Under "Temperature". Strip °C or *C, return numeric only.
   - **pulse_min:** Under "Pulse". Strip "/min", return numeric only.
   - **respiratory_min:** Under "Respiratory". Strip "/min", return numeric only.
   - **o2_sat:** Under "O2SAT". If no number is directly present, find the first numeric value near a /% symbol in the Nursing Assessment section. Return numeric only.
7. **visit_date / visit_time:** Find "Visit Date:" followed by DD/MM/YYYY then a 4-digit time. Split into separate fields. If the date separator is missing (e.g. "08/08 2020"), reconstruct as DD/MM/YYYY.
8. **disposition_date / disposition_time:** Find the table containing the "Disposition Done" column at the END of the record. Extract ONLY the date and time from that column. This is NOT the visit time, triage time, or any timestamp from Nursing Assessment or Observation Notes.
9. **pain_scale_score:** Find "Numerical(X)". Return only the integer X. Do not confuse with GCS.
10. **gcs:** Find the GCS value in the "Nursing Assessment" vitals section, typically "XX/15". Return only the numerator as a plain integer.
11. **triage_category:** Return only the number after "Triage Category:".
12. **past_history:** Find "Past History:" or "Past Medical History". Stop before "Travel History:" or any sidebar navigation text such as "HEMODIALYSIS", "LAB REPORTS", "OTHER DOCUMENTS", "ASSESSMENT/RE-ASSESSMENT".
13. **occupation:** Value after "Occupation:".
14. **marital_status:** Value after "Marital Status:".
15. **advice_health_education:** Find "Advice & Health Education:". Stop at "Education Given To:".
16. **condition_at_disposition:** Value after "Condition at the time of Disposition:" or "Condition at the tine of Disposition:".
17. **disposition_type:** Value after "Disposition Type:".
18. **remarks:** If remarks text is found after the Provisional Diagnosis table and before the Medication Order table, extract it and correct only obvious OCR spelling errors in individual words while preserving original sentence structure exactly. Otherwise return null.
19. **travel_history:** If the value is empty, a date, month-year, or any non-place text, return null. If "Travel History:" is immediately followed by another label, return null.
20. **current_medication:** Find "Current Medication". Stop at "Medical Prescription" or "Medication Order". If the section contains "No Important History" or is empty, return null. Do NOT extract from Medication Order, Medical Prescription, Injection Administration Log, or Care Plan.
21. **psychosocial:** Value after "Psychosocial:". Do not include occupation.
22. **disease_grouping:** Leave as null unless specified.
'''

paddle.set_flags({
"FLAGS_fraction_of_cpu_memory_to_use": 1.0,
"FLAGS_allocator_strategy": "naive_best_fit", # Optimize memory fragmentation
})

ocr_engine = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation= True,
    text_recognition_batch_size=2, 
    text_det_limit_side_len= 2000,
    text_det_limit_type= 'max',
    text_det_box_thresh= 0.5,
    text_det_thresh= 0.5,
    text_det_unclip_ratio=1.4, #Best results with 1.6
    lang='en',
    device= 'cpu',
    enable_mkldnn=True,
    mkldnn_cache_capacity=10,
    cpu_threads=4
    )

llm_engine = Llama(model_path= r"g:\models\qwen2.5-7b-instruct-q5_0-00001-of-00002.gguf",
                chat_format= "chatml",
                flash_attn= True,
                n_gpu_layers=-1,
                temperature= 0.2,
                seed= 1337,
                n_ctx= 8192,
                verbose= False)

service = Create_Service(CLIENT_FILE, API_NAME, API_VER, SCOPES)

parent_folder_id = get_ParentFolderId(body= service, 
                                      text= 'Elderly ER Data Pics')

subfolder_map = Search_Folder_with_names(body=service, parent_id=parent_folder_id)
subfolder_ids = sorted(subfolder_map.keys(), key=lambda fid: int(subfolder_map[fid].strip()))

for folder in subfolder_ids:
    comp_id = subfolder_map[folder].strip()
    print(comp_id)
    checkpoint = check_progress(checkpointfile)

    if checkpoint >= int(comp_id):
        print("Skipped")
        continue

    rows= specific_id_row(dataframe= file, specific_id= comp_id)
    image_ids = Search_Folder(body= service, parent_id= folder)
    image_bytes, pdf_bytes = get_image_bytes(image_file_ids= image_ids, service= service)

    texts = []
    readable_img = []
    pdf_texts = []
    if image_bytes:
        with ThreadPoolExecutor(max_workers=16) as Executor:
            if image_bytes:
                readable_img = list(Executor.map(new_edit_image, image_bytes))
            texts = list(Text_from_images(ocr= ocr_engine, readable_list= readable_img))

    elif pdf_bytes:
        for pdf_data in pdf_bytes:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete = False) as tmp:
                tmp.write(pdf_data)
                tmp_path = tmp.name
            try:
                result = ocr_engine.predict(tmp_path)
                for item in result:
                    texts_pdf = item.get('rec_texts', [])
                    pdf_texts.append("\n".join(texts_pdf))
            finally:
                os.unlink(tmp_path)
        texts = pdf_texts
    else:
        texts = []
    print("OCR done!")

    record = Record_Grouping_with_Dates(texts= texts)
    record = {key: value for key, value in record.items() if key != 'Unknown' or value}

    row_count_check = row_num_checker(rows= rows, total_records= record)
    row_data_check = check_row_data(rows= rows)
    if not row_data_check:
        continue
    copy_row_data = None
    if row_count_check > 0:
        new_row = max(row_data_check) + 3
        ws.insert_rows(new_row, row_count_check)
        copy_row_data = [cell.value for cell in ws[(max(row_data_check)+2)]]
        current_max = max(row_data_check)
        for j in range(1, row_count_check + 1):
            row_data_check.append(current_max + j)
    new_record = data_per_row(records= record, df= file, comp_id= comp_id)
    if not new_record:
        continue
    print("Cleaning Started!")
    clean_records = master_clean_ocr(records_dict= new_record)
    clean_noise_records = remove_sidebar_noise(records= clean_records)
    print(f"Records expected: {len(new_record)}, clean_noise_records: {len(clean_noise_records)}")

    primary_icd_list = list(find_primary_icd(clean_noise_records))

    print("LLM processing...")
    llm_step = list(llm_response(llm= llm_engine, 
                                 clean_records= clean_noise_records, 
                                 column_names= column_names, 
                                 prompt= prompt, 
                                 system_content= system_content, 
                                 primary_icd= primary_icd_list))
    for i,record in enumerate(llm_step):
        data = extract_json(record)

        regex_icd = primary_icd_list[i] if i < len(primary_icd_list) else None
        if regex_icd and data[22]:
            primary_code = data[22].split(' - ')[0].strip() if ' - ' in str(data[22]) else str(data[22])
            if regex_icd != primary_code:
                print(f"ICD mismatch comp {comp_id} record {i+1}: regex={regex_icd}, llm={primary_code}")
                with open("icd_mismatches.txt", "a") as f:
                    f.write(f"comp {comp_id} record {i+1}: regex={regex_icd}, llm={primary_code}\n")
                if ' - ' in str(data[22]):
                    desc = data[22].split(' - ', 1)[1]
                    data[22] = f"{regex_icd} - {desc}"
                else:
                    data[22] = regex_icd
        disp_date, disp_time = extract_last_datetime(clean_noise_records[i])
        print(f"Record {i+1} disposition regex result: {disp_date}, {disp_time}")
        
        final_date, final_time = pick_later_time(disp_date, disp_time, data[29], data[30])
        data[29] = final_date
        data[30] = final_time
        calculated_age = age_checker(age=None, dob=data[2], visit=data[3])
        if calculated_age:
            ws.cell(row=row_data_check[i] + 2, column=5, value=calculated_age)
        print(f"\n\nLLM Output for record {i+1}:\n{data}\n\n")
        add_data_to_excel(data= data, 
                          ws= ws, 
                          starting_column= 6, 
                          row_num= row_data_check[i], 
                          initial_data= copy_row_data 
                          if row_count_check > 0 else None)
    save_progress(checkpointfile, comp_id= comp_id)
    wb.save(filename= filepath)

end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(f"Took a total of {elapsed_time:.1f} seconds")