from DriveFunctions.Downloader import DownloadFiles
from concurrent.futures import ThreadPoolExecutor
from pillow_heif import register_heif_opener
register_heif_opener()
from PIL import Image
import io

def get_file_metadata(service, file_id):
    return service.files().get(fileId=file_id, fields='name, mimeType').execute()

def get_image_bytes(image_file_ids, service):
    if image_file_ids:
        image_ids = []
        pdf_ids = []
        converted_bytes = []
        heic_bytes = []
        for file_id in image_file_ids:
            meta = get_file_metadata(service, file_id)
            name = meta.get('name', '').lower()
            mime = meta.get('mimeType', '').lower()
            if name.endswith('.heic') or 'heic' in mime:
                response = service.files().get_media(fileId=file_id).execute()
                img = Image.open(io.BytesIO(response))
                img = img.convert('RGB')
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG')
                heic_bytes.append(buffer.getvalue())
            elif name.endswith('.pdf') or 'pdf' in mime:
                pdf_ids.append(file_id)
            else:
                image_ids.append(file_id)
        if not pdf_ids:
            converted_bytes = heic_bytes
        with ThreadPoolExecutor(max_workers=16) as executor:
            img_results = list(executor.map(DownloadFiles, image_ids)) if image_ids else []
            pdf_results = list(executor.map(DownloadFiles, pdf_ids)) if pdf_ids else []
        print(f"Done")
        return img_results + converted_bytes, pdf_results
    return [], []