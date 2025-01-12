from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

SERVICE_ACCOUNT_FILE = 'credentials/credentials.json'  # Ajuste o caminho se necessário
SCOPES = ['https://www.googleapis.com/auth/drive']
PARENT_FOLDER_ID = '1900p8OQqh_imzW8YDxA_gwHy5q81urZz'

def upload_to_drive(file_path, file_name):
    """Faz upload de um arquivo para o Google Drive."""
    creds = None
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    else:
        print(f"Erro: Arquivo de credenciais não encontrado em {SERVICE_ACCOUNT_FILE}")
        return None

    try:
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': file_name,
            'parents': [PARENT_FOLDER_ID]
        }
        media = MediaFileUpload(file_path, mimetype='application/pdf')
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f'Arquivo enviado com sucesso! ID: {file.get("id")}')
        return file.get('id')
    except Exception as e:
        print(f"Erro ao fazer upload do arquivo para o Google Drive: {e}")
        return None

def list_files_from_drive(filter_text):
    """Lista os arquivos do Google Drive que correspondem ao filtro."""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    query = f"'{PARENT_FOLDER_ID}' in parents"
    if filter_text:
        query += f" and name contains '{filter_text}'"

    results = service.files().list(q=query, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    return items