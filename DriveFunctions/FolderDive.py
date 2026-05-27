# from Google import Create_Service
import pandas as pd

def get_id(get:object, params:str, identifier:str, include_names:bool=False):
    service = get
    param = params
    folder_identifier = identifier
    query = f"{param} = '{folder_identifier}' and trashed = false"

    response = (service.files()
                .list(q= query, orderBy = 'name_natural', 
                      fields = 'nextPageToken, files(id, name)')
                .execute())
    files = response.get('files')
    nextPageToken = response.get('nextPageToken')

    while nextPageToken:
        response = (service.files()
                    .list( q= query,
                           orderBy= 'name_natural', 
                           fields = 'nextPageToken, files(id, name)',
                           pageToken= nextPageToken )
                    .execute())
        files.extend(response.get('files'))
        nextPageToken = response.get('nextPageToken')

    if files != []:
        df = pd.DataFrame(files)
        if include_names:
            return dict(zip(df['id'], df['name']))
        return df['id'].to_list()
    return {} if include_names else None

def get_ParentFolderId(body: object, text:str):
    service = body
    folder_name = text
    query_type = 'name' # runs query parameter for name using given folder name

    request = get_id(get= service, 
                     params= query_type, 
                     identifier= folder_name)
    for item in request:
        return item

def Search_Folder(body:object, parent_id:str):
    service = body
    folder_id = parent_id
    query_type = 'parents'

    request = get_id(get= service, params= query_type, identifier= folder_id)
    return request

def Search_Folder_with_names(body:object, parent_id:str):
    return get_id(get=body, params='parents', identifier=parent_id, include_names=True)

def get_folder_name(body, folder_id):
    request = body.files().get(fileId= folder_id, fields='name').execute()
    name = request['name']
    return name
