import re

def load_icd_codes(filepath):
    valid_codes = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(';')
            if len(parts) >= 6:
                code = parts[5].strip().replace('.', '').replace('-', '')
                if re.match(r'^[A-Z]\d{2}', code):
                    valid_codes.add(code)
    valid_prefixes = {c[:3] for c in valid_codes}
    return valid_codes, valid_prefixes

def validate_icd(code, valid_codes, valid_prefixes):
    if not code:
        return False
    normalized = code.strip().replace('.', '')
    if normalized in valid_codes:
        return True
    if normalized[:3] in valid_prefixes:
        return True
    return False

def filter_other_icd(codes_string, valid_codes, valid_prefixes, comp_id, record_num):
    if not codes_string:
        return None
    codes = [c.strip() for c in codes_string.split(',')]
    valid = []
    invalid = []
    for code in codes:
        if validate_icd(code, valid_codes, valid_prefixes):
            valid.append(code)
        else:
            invalid.append(code)
    if invalid:
        with open("invalid_icds.txt", "a") as f:
            f.write(f"comp {comp_id} record {record_num}: invalid codes removed: {', '.join(invalid)}\n")
        print(f"Invalid ICD codes removed for comp {comp_id} record {record_num}: {invalid}")
    return ', '.join(valid) if valid else None