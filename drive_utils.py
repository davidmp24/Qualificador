from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import json

def get_drive_credentials():
    """Obtém as credenciais do Google Drive a partir da variável de ambiente."""
    credentials_json_str = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    if credentials_json_str:
        # Carrega as credenciais a partir da string JSON
        credentials_info = json.loads(credentials_json_str)
        creds = service_account.Credentials.from_service_account_info(credentials_info)
        return creds
    else:
        raise ValueError("Variável de ambiente GOOGLE_APPLICATION_CREDENTIALS não definida!")

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
    """Lista os arquivos do Google Drive com base em um filtro."""
    creds = get_drive_credentials() # Use a função para obter as credenciais
    service = build('drive', 'v3', credentials=creds)

    # Adapte a consulta de acordo com suas necessidades
    query = f"name contains '{filter_text}' and mimeType != 'application/vnd.google-apps.folder'"
    results = service.files().list(q=query, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    return items
