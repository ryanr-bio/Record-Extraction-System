from DriveFunctions.Downloader import DownloadFiles
from concurrent.futures import ThreadPoolExecutor

def get_file_metadata(service, file_id):
    return service.files().get(fileId=file_id, fields='name, mimeType').execute()

def get_image_bytes(image_file_ids, service):
    if image_file_ids:
        filtered_ids = []
        for file_id in image_file_ids:
            meta = get_file_metadata(service, file_id)
            name = meta.get('name', '').lower()
            mime = meta.get('mimeType', '').lower()
            if name.endswith('.heic') or 'heic' in mime:
                print(f"Skipping HEIC file: {meta.get('name')}")
                continue
            filtered_ids.append(file_id)

        with ThreadPoolExecutor(max_workers=16) as executor:
            results = list(executor.map(DownloadFiles, filtered_ids))
            print(f"Done")
            return results
