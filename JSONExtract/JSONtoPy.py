import datetime
import json
import re
import pandas as pd

def fix_icd_misread(code: str) -> str:
    if not isinstance(code, str):
        return None
    code = code.strip()
    if len(code) >= 3 and code[0].isalpha():
        code = code[0] + code[1:].replace('O', '0')
    if re.match(r'^L[A-Z]\d', code):
        code = code[1:]
    if re.match(r'^2\d{2}', code):
        code = 'Z' + code[1:]
    if re.match(r'^Z0\.\d+$', code):
        code = 'Z00' + code[2:]
    if re.match(r'^O\d{1,2}', code):
        code = 'Z' + code[1:]
    if re.match(r'^1\d{2}', code):
        code = 'I' + code[1:]
    if re.match(r'^Z0[2-9]\d$', code):
        return None
    if not re.match(r'^[A-Z]\d', code):
        return None
    return code

def format_time(t):
    if isinstance(t, str):
        t = t.strip().replace(":", "")
        if len(t) == 4 and t.isdigit():
            return f"{t[:2]}:{t[2:]}"
    return t

def age_checker(age, dob, visit):
    if not dob or not visit:
        print("Date is not given properly")
        return
    try:
        birth_date = datetime.datetime.strptime(dob, "%d/%m/%Y")
        visit_date = datetime.datetime.strptime(visit, "%d/%m/%Y")
        birth_year = birth_date.year
        birth_month = birth_date.month
        birth_day = birth_date.day
        visit_year = visit_date.year
        age_year = visit_year - birth_year
        check_birthday = datetime.datetime(visit_year, birth_month, birth_day)
        if check_birthday > visit_date:
            age = age_year - 1
        else:
            age = age_year
        
    except ValueError:
        print(f"Could not parse dates: dob={dob}, visit={visit}")
    return age

def strip_braces(value):
    if isinstance(value, str):
        return value.strip('{}').strip()
    return value

def validate_vitals(data):
    try:
        temp = float(data[5]) if data[5] else None
        if temp and temp > 45:
            data[5] = str(round(temp / 10, 1))
    except (ValueError, TypeError):
        pass
    try:
        resp = float(data[7]) if data[7] else None
        if resp and resp > 60:
            data[7] = None
    except (ValueError, TypeError):
        pass
    try:
        triage = int(data[15]) if data[15] else None
        if triage is None or not (1 <= triage <= 5):
            data[15] = None
    except (ValueError, TypeError):
        data[15] = None
    try:
        bp = data[8] if len(data) > 8 else None
        if bp and not re.match(r'^\d{2,3}/\d{2,3}$', str(bp).strip()):
            data[8] = None
    except (ValueError, TypeError):
        data[8] = None
    return data

def extract_json(llm_output):
    try:
        jsondict = json.loads(llm_output)
        list_of_patterns = [r"marital", r"nationality", r"date_of_birth",
                            r"visit_date", r"visit_time", r"temperature", r"pulse", 
                            r"respiratory", r"bp", r"o2", r"pain_scale", r"gcs", 
                            r"height", r"weight", r"bmi", r"triage", r"chief", 
                            r"past", r"travel", r"medication", r"psychosocial", 
                            r"occupation", r"primary", r"other", r"disease", 
                            r"remarks", r"disposition_type", r"advice", r"condition", 
                            r"disposition_date", r"disposition_time"]

        for key in jsondict:
            if re.search(r"primary", key):
                jsondict[key] = fix_icd_misread(jsondict[key])
            elif re.search(r"other", key):
                if isinstance(jsondict[key], str):
                    print(f"Raw other_icd from LLM: {jsondict[key]}")
                    primary_code = (jsondict.get("primary_icd") or "").split(" - ")[0].strip()
                    codes = jsondict[key].split(",")
                    fixed = [fix_icd_misread(c.strip()) for c in codes]
                    jsondict[key] = ", ".join(
                        c for c in fixed 
                        if c is not None and c != primary_code
                    )
            if re.search(r"time", key):
                jsondict[key] = format_time(jsondict[key])

        values = []
        for variable in jsondict.keys():
            for pattern in list_of_patterns:
                if re.search(pattern=pattern, string=variable):
                    values.append(jsondict[variable])
                    break 
        values = [strip_braces(v) for v in values]
        values = validate_vitals(values)
        return values
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        print(f"Raw LLM output:\n{llm_output}")
        return None

def extract_last_datetime(record_text):
    dt_pattern = r"(\d{2}/\d{2}/\d{2,4})\s*(\d{2}:\d{2}|\d{4})"
    for anchor in [r"Disposition\s+Disposition\s+Done", r"Disposition\s+Date", r"Disposition\s+Details"]:
        disp_section = re.search(anchor + ".*", record_text, re.DOTALL | re.IGNORECASE)
        if disp_section:
            break
    if not disp_section:
        return None, None
    
    matches = re.findall(dt_pattern, disp_section.group())
    if not matches:
        return None, None

    latest = None
    latest_dt = None
    for date_str, time_str in matches:
        if ":" not in time_str and len(time_str) == 4:
            time_str_parsed = f"{time_str[:2]}:{time_str[2:]}"
        else:
            time_str_parsed = time_str

        try:
            dt = pd.to_datetime(f"{date_str} {time_str_parsed}", dayfirst=True, errors='coerce')
            if pd.notna(dt) and (latest_dt is None or dt > latest_dt):
                latest_dt = dt
                latest = (date_str, time_str_parsed)
        except:
            pass
    return latest if latest else (None, None)

def pick_later_time(regex_date, regex_time, llm_date, llm_time):
    try:
        regex_dt = pd.to_datetime(f"{regex_date} {regex_time}", dayfirst=True, errors='coerce')
        llm_dt = pd.to_datetime(f"{llm_date} {llm_time}", dayfirst=True, errors='coerce')
        if pd.isna(regex_dt) and pd.isna(llm_dt):
            return llm_date, llm_time
        if pd.isna(regex_dt):
            return llm_date, llm_time
        if pd.isna(llm_dt):
            return regex_date, regex_time
        if regex_dt >= llm_dt:
            return regex_date, regex_time
        else:
            return llm_date, llm_time
    except:
        return llm_date, llm_time

def validate_disposition(data, comp_id=None, record_num=None):
    try:
        visit_date = data[3]
        disp_date = data[29]
        disp_time = data[30]
        
        if not visit_date or not disp_date:
            return data
            
        visit_dt = pd.to_datetime(visit_date, dayfirst=True, errors='coerce')
        disp_dt = pd.to_datetime(f"{disp_date} {disp_time}" if disp_time else disp_date, 
                                  dayfirst=True, errors='coerce')
        
        if pd.isna(visit_dt) or pd.isna(disp_dt):
            return data
            
        # Disposition should be after visit and within 30 days
        diff = (disp_dt - visit_dt).days
        if diff < 0 or diff > 30:
            print(f"Suspicious disposition date: visit={visit_date}, disp={disp_date}")
            with open("disposition_errors.txt", "a") as f:
                f.write(f"comp {comp_id} record {record_num}: visit={visit_date}, disp={disp_date} {disp_time}\n")
            data[29] = None
            data[30] = None
            
    except Exception:
        pass
    return data