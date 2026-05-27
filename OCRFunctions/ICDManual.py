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

        icd_pattern = r"[A-Z]\d{2,3}\.?\d*|1\d{2}\.?\d*|2\d{2}\.?\d*"
        verified_pattern = r"(?:Not\s+)?V[ae]?[rn]?[ie]?f?i?e?d"
        matched = None
        all_lines = section.split("\n")

        for idx, line in enumerate(all_lines):
            if re.search(r"Care Plan|Medication Order|Observation Notes", line, re.IGNORECASE):
                break
            if not re.search(r"\bYes\b", line, re.IGNORECASE):
                continue

            # Get surrounding context window (2 lines before, current, 2 lines after)
            window_start = max(0, idx - 2)
            window_end = min(len(all_lines), idx + 3)
            window = all_lines[window_start:window_end]
            window_text = "\n".join(window)

            # Only proceed if verified marker is in the window
            if not re.search(verified_pattern, window_text, re.IGNORECASE):
                continue

            # Try same line first
            icd_match = re.search(icd_pattern, line)

            # Then look backwards up to 5 lines
            if not icd_match:
                for prev in reversed(all_lines[max(0, idx-5):idx]):
                    icd_match = re.search(icd_pattern, prev)
                    if icd_match:
                        break

            # Then look forwards up to 3 lines
            if not icd_match:
                for next_line in all_lines[idx+1:idx+4]:
                    icd_match = re.search(icd_pattern, next_line)
                    if icd_match:
                        break

            if icd_match:
                matched = fix_icd_misread(icd_match.group())
                break

        yield matched