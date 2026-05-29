import re

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

def llm_response(llm, clean_records, prompt, system_content, column_names, primary_icd):
    if clean_records:
        schema = create_json_template(column_names)
        icd_list = primary_icd
        if len(icd_list) < len(clean_records):
            icd_list += [None] * (len(clean_records) - len(icd_list))
        for ocr_result, icd in zip(clean_records, icd_list):
            icd_instruction = f"\n### PRIMARY ICD (already extracted, do not change):\nThe primary_icd field must be set to: '{icd} - [find the matching description from the Provisional Diagnosis table]'" if icd else ""
            response = llm.create_chat_completion(
                messages=[
                    {
                        "role":"system",
                        "content":system_content
                    },
                    {
                        "role":"user",
                        "content":f'''{prompt}{icd_instruction}
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
                max_tokens=-1,
                temperature= 0.2
            )
            output = response["choices"][0]["message"]["content"]
            yield output