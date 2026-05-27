from DriveFunctions.Downloader import DownloadFiles
from concurrent.futures import ThreadPoolExecutor

def get_file_metadata(service, file_id):
    return service.files().get(fileId=file_id, fields='name, mimeType').execute()

def get_image_bytes(image_file_ids, service):
    if image_file_ids:
        image_ids = []
        pdf_ids = []
        for file_id in image_file_ids:
            meta = get_file_metadata(service, file_id)
            name = meta.get('name', '').lower()
            mime = meta.get('mimeType', '').lower()
            if name.endswith('.heic') or 'heic' in mime:
                print(f"Skipping HEIC file: {meta.get('name')}")
                continue
            elif name.endswith('.pdf') or 'pdf' in mime:
                pdf_ids.append(file_id)
            else:
                image_ids.append(file_id)

        with ThreadPoolExecutor(max_workers=16) as executor:
            img_results = list(executor.map(DownloadFiles, image_ids)) if image_ids else []
            pdf_results = list(executor.map(DownloadFiles, pdf_ids)) if pdf_ids else []
        print(f"Done")
        return img_results, pdf_results
    return [], []