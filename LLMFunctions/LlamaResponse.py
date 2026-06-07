import re
from llama_cpp import Llama

def create_json_template(column_names):
    template = {}
    d = {" ": "_", "/": "", "(": "", ")": "", "&": ""}
    for col in column_names:
        col = re.sub(r"[\s&]|[\(\)\/]", lambda x: d[x[0]], col)
        template[col] = {"type": ["string", "null"]}
    
    return {
        "type": "object",
        "properties": template,
        "required": list(template.keys())
    }

def llm_response(llm, clean_records, prompt, system_content, column_names, primary_icd, other_icd_list, remarks_list):
    if clean_records:
        schema = create_json_template(column_names)
        icd_list = primary_icd
        if len(icd_list) < len(clean_records):
            icd_list += [None] * (len(clean_records) - len(icd_list))
        for ocr_result, icd, other_icd, remark in zip(clean_records, icd_list, other_icd_list, remarks_list):
            llm.reset()
            icd_instruction = f"\n### PRIMARY ICD (regex suggestion: {icd}):\nThe regex has detected '{icd}' as the likely primary ICD. Verify this against the Provisional/Final Diagnosis table. If correct, return it with its description as 'Code - Description'. If incorrect or not found, return the actual primary ICD code with description from the table." if icd else "\n### PRIMARY ICD: Find the ICD code marked as Primary ICD or has 'Yes' in the Provisional/Final Diagnosis table and return as 'Code - Description'." 
            other_icd_instruction = f"\n### OTHER ICD (already extracted, do not change):\nThe other_icd field must be set to: '{other_icd}'" if other_icd else "\n### OTHER ICD: Set other_icd to null if no codes found."
            remarks_instruction = f"\n### REMARKS (already extracted, do not change):\nThe remarks field must be set to: '{remark}'" if remark else "\n### REMARKS: Set remarks to null."
            response = llm.create_chat_completion(
                messages=[
                    {
                        "role":"system",
                        "content":system_content
                    },
                    {
                        "role":"user",
                        "content":f'''{prompt}{icd_instruction}{other_icd_instruction}{remarks_instruction}
                        ### OUTPUT: 
                        Return ONLY raw JSON. No explanation, no markdown, no 
                        preamble.
                        Do not write markdown block quotes (such as ```json). Do not truncate.
                        OCR Text:
                        {ocr_result}'''
                    }
                ],
                response_format={
                    "type": "json_object",
                    "schema": schema
                },
                max_tokens= None,
                temperature= 0.2
            )
            output = response["choices"][0]["message"]["content"]
            yield output