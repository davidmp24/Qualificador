from flask import Flask, render_template, request, redirect, url_for, send_file
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import time
import uuid

# Importe a função do arquivo drive_utils.py (crie esse arquivo se ainda não existir)
from drive_utils import list_files_from_drive, upload_to_drive

app = Flask(__name__)

# Configurações para o Google Drive
SERVICE_ACCOUNT_FILE = 'credentials.json'
if not os.path.exists(SERVICE_ACCOUNT_FILE):
  with open(SERVICE_ACCOUNT_FILE, 'w') as f:
    f.write(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))
SCOPES = ['https://www.googleapis.com/auth/drive']
PARENT_FOLDER_ID = '1900p8OQqh_imzW8YDxA_gwHy5q81urZz'  # <----- COLOQUE O ID DA SUA PASTA AQUI

# Configurações do app
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def inicial():
    return render_template("inicial.html")

@app.route('/qualificacao', methods=['GET'])
def qualificacao():
    dados = {
        'nome': request.args.get('nome'),
        'vulgo': request.args.get('vulgo'),
        'rgcpf': request.args.get('rgcpf'),
        'ssp': request.args.get('ssp'),
        'nascimento': request.args.get('nascimento'),
        'natureza': request.args.get('natureza'),
        'datafato': request.args.get('datafato'),
        'bopme': request.args.get('bopme'),
        'foto_url': request.args.get('foto_url'),
        'cidade': request.args.get('cidade'),
        'endereco': request.args.get('endereco')
    }
    return render_template('qualificacao.html', **dados)

@app.route('/resultado', methods=['POST'])
def resultado():
    dados = {
        'nome': request.form.get('nome'),
        'vulgo': request.form.get('vulgo'),
        'rgcpf': request.form.get('rgcpf'),
        'ssp': request.form.get('ssp'),
        'nascimento': request.form.get('nascimento'),
        'natureza': request.form.get('natureza'),
        'datafato': request.form.get('datafato'),
        'bopme': request.form.get('bopme'),
        'cidade': request.form.get('cidade'),
        'endereco': request.form.get('endereco')
    }

    foto = request.files.get('foto')
    foto_url = None

    if foto and foto.filename != '':
        filename = os.path.basename(foto.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        foto.save(file_path)
        foto_url = url_for('static', filename=f'uploads/{filename}')

    return render_template('resultado.html', **dados, foto_url=foto_url)

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    """Recebe o PDF do cliente, faz upload para o Google Drive e o envia para download."""
    try:
        pdf_file = request.files.get('pdf')
        nome = request.form.get('nome')

        if pdf_file and pdf_file.filename != '' and nome:
            pdf_filename = f"{nome.replace(' ', '_')}.pdf"
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)

            # Salvar o PDF temporariamente
            pdf_file.save(pdf_path)

            # Fazer upload para o Google Drive
            file_id = upload_to_drive(pdf_path, pdf_filename)
            if file_id:
                print(f"PDF salvo no Google Drive com ID: {file_id}")
            else:
                print("Falha ao fazer upload do PDF para o Google Drive.")

            # Enviar o PDF para download
            return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)

        else:
            return 'Nenhum arquivo PDF ou nome recebido.', 400
    except Exception as e:
        print(f"Erro ao processar o PDF: {e}")
        return "Erro ao processar o PDF", 500

@app.route('/editar_qualificado', methods=['GET', 'POST'])
def editar_qualificado():
    if request.method == 'GET':
        dados = {
            'nome': request.args.get('nome'),
            'vulgo': request.args.get('vulgo'),
            'rgcpf': request.args.get('rgcpf'),
            'ssp': request.args.get('ssp'),
            'nascimento': request.args.get('nascimento'),
            'natureza': request.args.get('natureza'),
            'datafato': request.args.get('datafato'),
            'bopme': request.args.get('bopme'),
            'foto_url': request.args.get('foto_url'),
            'cidade': request.args.get('cidade'),
            'endereco': request.args.get('endereco')
        }
        return render_template('editar_qualificado.html', **dados)

    if request.method == 'POST':
        dados = {
            'nome': request.form.get('nome'),
            'vulgo': request.form.get('vulgo'),
            'rgcpf': request.form.get('rgcpf'),
            'ssp': request.form.get('ssp'),
            'nascimento': request.form.get('nascimento'),
            'natureza': request.form.get('natureza'),
            'datafato': request.form.get('datafato'),
            'bopme': request.form.get('bopme'),
            'cidade': request.form.get('cidade'),
            'endereco': request.form.get('endereco')
        }

        foto = request.files.get('foto')
        foto_removida = request.form.get('foto_removida')
        foto_url = request.form.get('foto_url')

        if foto_removida == 'true':
          foto_url = None
        elif foto and foto.filename != '':
            filename = os.path.basename(foto.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(file_path)
            foto_url = url_for('static', filename=f'uploads/{filename}')

        return render_template('resultado.html', **dados, foto_url=foto_url)

@app.route('/consulta', methods=['GET', 'POST'])
def consulta():
    filter_text = ""
    if request.method == 'POST':
        filter_text = request.form.get('filter_text', '')

    # Chame a função importada de drive_utils.py
    files = list_files_from_drive(filter_text)

    return render_template('consulta.html', files=files, filter_text=filter_text)

@app.route('/visualizar/<file_id>')
def visualizar(file_id):
    """Busca o arquivo no Google Drive e o envia diretamente para o navegador."""
    creds = None
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    else:
        print(f"Erro: Arquivo de credenciais não encontrado em {SERVICE_ACCOUNT_FILE}")
        return "Erro: Arquivo de credenciais não encontrado.", 500

    try:
        service = build('drive', 'v3', credentials=creds)

        # Obter metadados do arquivo, incluindo o nome
        file_metadata = service.files().get(fileId=file_id, fields='name').execute()
        file_name = file_metadata.get('name')

        # Montar o caminho do arquivo local
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

        # Verificar se o arquivo existe localmente
        if os.path.exists(file_path):
            # Enviar o arquivo para download com o nome original
            return send_file(file_path, as_attachment=True, download_name=file_name)
        else:
            print(f"Arquivo não encontrado localmente: {file_path}")
            return "Arquivo não encontrado.", 404

    except Exception as e:
        print(f"Erro ao buscar arquivo: {e}")
        return f"Erro ao buscar arquivo: {e}", 500

@app.route('/informacao')
def informacao():
    return render_template('informacao.html')

if __name__ == "__main__":
    app.run(debug=True)