import re

def clean_ocr(records_dict):
    if not records_dict:
        return
    list_of_patterns = [ r"Primary ICD", r"mobile no[\W] \d{10}", 
                    r"file[\W|\s]no[\W] \d{2}[\W]\d{2}[\W]\d{2}", 
                    r"appt[\W]\s?time:", r"department[\W] accident and emergency", 
                    r"ND EMERGENCY", r"Fall Risk Assesment", 
                    r"Vital Reasses?s?ment", 
                    r"Fall Risk Reasses?s?ment", r"Nurse\W?s Note Reassessment", 
                    r"NCY\(\d*\)?", r"EPORTS",
                    r"\S*[\W]thumbay[\W]int\S*", r"PVR\s?ID[\W] \d{6}", 
                    r"I?DENT AND EMERGE", r"\S*\(\d*-(\s?\d*\)?)", 
                    r"Thumbay University", r"EMERGEN",
                    r"Generic\s?Name\s?Brand\s?\s?All\s?Instructions\s?Route", 
                    r"\s?Administrated\s?on\s?(No\s?)?Administrated\s?By", 
                    r"\s?Service\s?id[\W]\s?", r"CPTCODE[\W]\s?\d*[\W]",
                    r"(\w*)?\W?(\w*)?\W?(\w*)?(\W*)?(\w*)?(\W*)?(\w*)?/W(\d*)?\W(\w*)?\W(\w*)?", 
                    r"\w*[\W]studentpharma\s"] #r"[\W]\d*[\W]\d*[\W]\s\d*",
    
    patterns = "|".join(list_of_patterns)
    
    compiled = re.compile(pattern= patterns, flags= re.IGNORECASE)
    cleanest = []
    for value in records_dict.values():
        clean = re.sub(pattern= compiled, repl= "", 
                       string= value)
        cleanest.append(clean)
    return cleanest

def master_clean_ocr(records_dict):
    removals = [
        (r"Fall\s*Risk\s*(?:Re)?as+es+ment", r"Chief Complaint"),
        (r"Menstrual\s*History", r"Past History"),
        (r"Nurs\w*\s+Not\w+", r"Travel History"),
        (r"Problems[\s\n]+(?:SI\.?\s*No|Life Cycle)", r"Care Plan"),
        (r"Medication\s*Order", r"Disposition"),
        (r"Vital\s*Re-?as+es+ment", r"(?:Functional|Nutritional?)\s*(?:Assessment|Screening)|Suicide\s*(?:Threat|Risk)|Allerg(?:y|ies)"),
    ]
    
    cleaned_records = {}
    for key, value in records_dict.items():
        combined_patient_text = "\n\n".join(value)

        for start_pattern, end_anchor in removals:
            pattern = rf"(?i){start_pattern}.*({end_anchor})"
            combined_patient_text = re.sub(pattern, r"\1", combined_patient_text, flags=re.DOTALL)
            
        cleaned_records[key] = re.sub(r"\n{3,}", "\n\n", combined_patient_text)
        
    total_clean = clean_ocr(cleaned_records)
    return total_clean

def remove_sidebar_noise(records):
    if not records:
        return records
    
    SIDEBAR_NOISE = [
        "Doctor", "All", "ACC", "MEDICAL RECORDS", "LAB REPORTS", "RADIOLOGY REPORTS",
        "OTHER REPORTS", "OTHER DOCUMENTS", "OTHER FILES", 
        "HEMODIALYSIS - NUTRITION", "ASSESSMENT/RE-ASSESSMENT", 
        "VisitRecord", "Departmet", "isil Type", "isit Type",
        "©All OP IP", "©AlI OP IP", ":AL OP OIP", "All OP IP",
        "74U10", "74010", "7AU10", "34U1C", "D4U10", "G002", "L002", 
        "L602", "2072", "2032", "2202", "4032", "C73", "Z022", "OIV12", 
        "GI010", "C033", "URULOO", "UAULUO", "UAVLVUT", "JURULVO",
    ]
    
    cleaned_records = []
    for record in records:
        lines = record.split('\n')
        cleaned = [
            line for line in lines
            if not any(noise in line.strip() for noise in SIDEBAR_NOISE)
            and not re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}\)?$', line.strip())
        ]
        cleaned_records.append('\n'.join(cleaned))
    return cleaned_records