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

        icd_pattern = r"[A-Z]\d{1,3}\.?\d*|1\d{2}\.?\d*|2\d{2}\.?\d*"
        matched = None
        prev_lines = []
        all_lines = section.split("\n")

        for idx, line in enumerate(all_lines):
            if re.search(r"\bYes\b", line, re.IGNORECASE):
                icd_match = re.search(icd_pattern, line)
                if not icd_match:
                    for prev in reversed(prev_lines[-5:]):
                        icd_match = re.search(icd_pattern, prev)
                        if icd_match:
                            break
                if not icd_match:
                    for next_line in all_lines[idx+1:idx+4]:
                        icd_match = re.search(icd_pattern, next_line)
                        if icd_match:
                            break
                if icd_match:
                    matched = fix_icd_misread(icd_match.group())
                    break
            prev_lines.append(line)
        yield matched