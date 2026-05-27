import io
import re
import cv2 as cv
import numpy as np

def new_edit_image(img_bytes):
    if not img_bytes:
        return None
    try:
        image_bytes = io.BytesIO(img_bytes)
        nparr = np.frombuffer(image_bytes.read(), np.uint8)
        img = cv.imdecode(nparr, cv.IMREAD_COLOR)
        if img is None:
            print(f"Could not decode image, skipping")
            return None
        sharp_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        resized_img = cv.resize(img, (1920, 1080))
        resized_img = cv.GaussianBlur(resized_img, (7, 7), 0)
        resized_img = cv.filter2D(resized_img, -1, sharp_kernel)
        return resized_img
    except Exception as e:
        print(f"Image processing failed: {e}")
        return None

def Text_from_images(ocr, readable_list):
    results = ocr.predict_iter(readable_list)
    for item in results:
        texts = item.get('rec_texts', [])
        string = "\n".join(texts)
        yield string

def Record_Grouping_with_Dates(texts):
    record_groups = {"Unknown": []}
    current_key = "Unknown"
    query = r"Visit\s*Date\W{0,3}(\d{2})\W{0,3}(\d{2})\W{0,3}(\d{4})"

    for records in texts:
        search = re.search(query, records, re.IGNORECASE)
        if search:
            key = search.groups()
            clean_key = " ".join(key)
            if clean_key not in record_groups.keys():
                record_groups[clean_key] = []
            record_groups[clean_key].append(records)
            current_key = clean_key
        else:
            record_groups[current_key].append(records)
    return record_groups