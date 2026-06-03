import re
from JSONExtract.JSONtoPy import fix_icd_misread

def find_primary_icd(records):
    for record in records:
        section = None
        for header in ["Provisional Diagnosis", "Primary ICD", "Final Diagnosis"]:
            idx = record.rfind(header)
            if idx != -1:
                section = record[idx:]
                break
        if section is None:
            yield None
            continue

        icd_pattern = r"\b[A-Z]\d{2,3}\.?\d*\b"
        matched = None
        all_lines = section.split("\n")

        for idx, line in enumerate(all_lines):
            if re.search(r"Care Plan|Medication Order|Observation Notes", line, re.IGNORECASE):
                break
            if not re.search(r"\bYes\b", line, re.IGNORECASE):
                continue

            not_verified_idx = None
            for back_idx in range(idx - 1, max(0, idx - 6) - 1, -1):
                if re.search(r"(?:Not\s*|MRD\s*)Verified|Venified", all_lines[back_idx], re.IGNORECASE):
                    not_verified_idx = back_idx
                    break

            if not_verified_idx is None:
                continue

            icd_match = None
            for search_idx in range(idx, -1, -1):
                search_line = all_lines[search_idx]
                
                matches = list(re.finditer(icd_pattern, search_line))
                if matches:
                    for match in reversed(matches):
                        start = match.start()
                        if start > 0 and search_line[start - 1].isalpha():
                            continue  
                        
                        icd_match = match
                        break
                
                if icd_match:
                    break

            if icd_match:
                matched = fix_icd_misread(icd_match.group())
                break

        yield matched

def find_other_icd(records, primary_icd_list):
    for record, primary_icd in zip(records, primary_icd_list):
        section = None

        for header in ["Provisional Diagnosis", "Final Diagnosis"]:
            idx = record.rfind(header)
            if idx != -1:
                section = record[idx:]
                break
                
        if section is None:
            yield None
            continue

        end_section_match = re.search(r"Care\s*Plan|Medication\s*Order|Observation\s*Notes", section, re.IGNORECASE)
        if end_section_match:
            section = section[:end_section_match.start()]

        icd_pattern = r"\b[A-Z]\d{2,3}\.?\d*\b"
        primary_code = primary_icd.split(' - ')[0].strip() if primary_icd and ' - ' in primary_icd else primary_icd

        found_codes = re.findall(icd_pattern, section)
        other_codes = []
        
        for match in found_codes:
            fixed = fix_icd_misread(match)
            if fixed and fixed != primary_code and fixed not in other_codes:
                other_codes.append(fixed)

        yield ", ".join(other_codes) if other_codes else None

def find_remarks(records):
    for record in records:
        remarks_match = re.search(r"Remarks\s*:", record, re.IGNORECASE)
        if not remarks_match:
            yield None
            continue
        
        start = remarks_match.end()
        
        end_match = re.search(
            r"Medical\s*Prescription|Medication\s*Order|Disposition|Advice\s*&\s*Health|Problems", 
            record[start:], re.IGNORECASE
        )
        
        if end_match:
            text = record[start:start + end_match.start()].strip()
        else:
            text = record[start:].strip()
            
        text = re.sub(r"\s*[\+\-\|]\s*", " ", text)
        text = re.sub(r"\n+", " ", text).strip()
        
        yield text if text else None
