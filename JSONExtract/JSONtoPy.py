import datetime
import json
import re
import pandas as pd

def fix_icd_misread(code: str) -> str:
    if not isinstance(code, str):
        return None
    code = code.strip()
    if re.match(r'^L[A-Z]\d', code):
        return code[1:]
    if re.match(r'^2\d{2}', code):
        return 'Z' + code[1:]
    if re.match(r'^O\d{1,2}', code):
        return 'Z' + code[1:]
    if re.match(r'^1\d{2}', code):
        return 'I' + code[1:]
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
    return data

def extract_json(llm_output):
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
                codes = jsondict[key].split(",")
                fixed = [fix_icd_misread(c.strip()) for c in codes]
                jsondict[key] = ", ".join(c for c in fixed if c is not None)
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

def extract_last_datetime(record_text):
    dt_pattern = r"(\d{2}/\d{2}/\d{2,4})\s*(\d{2}:\d{2})"
    disp_section = re.search(
        r"Disposition Date.*",
        record_text,
        re.DOTALL | re.IGNORECASE
    )
    if not disp_section:
        return None, None
    
    matches = re.findall(dt_pattern, disp_section.group())
    if not matches:
        return None, None

    latest = None
    latest_dt = None
    for date_str, time_str in matches:
        try:
            dt = pd.to_datetime(f"{date_str} {time_str}", dayfirst=True, errors='coerce')
            if dt and (latest_dt is None or dt > latest_dt):
                latest_dt = dt
                latest = (date_str, time_str)
        except:
            pass
    return latest if latest else (None, None)