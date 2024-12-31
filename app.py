import os
import time
import random
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', '93096627')

# Configurações do app
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Função para verificar a extensão do arquivo
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf'}

# Função para gerar um nome de arquivo seguro
def generate_safe_filename(filename):
    return secure_filename(filename)

# Função para gerar o PDF
def generate_pdf(dados, pdf_filepath, foto_url=None):
    doc = SimpleDocTemplate(pdf_filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []

    # Adiciona a logo
    logo_path = 'static/images/logoapp.png'
    if os.path.exists(logo_path):
        logo = Image(logo_path, 1*inch, 1*inch)
        Story.append(logo)
    else:
        Story.append(Paragraph("Logo não encontrada", styles["Normal"]))

    Story.append(Paragraph(" ", styles["Normal"]))

    # Adicionar texto centralizado
    Story.append(Paragraph("<u><b>BOLETIM DE OCORRÊNCIA POLICIAL MILITAR ELETRÔNICO - BOPM-E</b></u>", styles["Heading1"]))
    Story.append(Paragraph(" ", styles["Normal"]))
    Story.append(Paragraph("<i><b>POLÍCIA MILITAR DO ESTADO DE SÃO PAULO - 24º BPM/I - 1ª CIA PM</b></i>", styles["Heading2"]))
    Story.append(Paragraph(" ", styles["Normal"]))
    Story.append(Paragraph("<i><b>QUALIFICAÇÃO DE PESSOAS</b></i>", styles["Heading3"]))
    Story.append(Paragraph(" ", styles["Normal"]))

    # Exemplo de como adicionar os dados ao PDF
    data = [
        ["Batalhão", dados['batalhao']],
        ["CIA", dados['cia']],
        ["Pel / GP", dados['pelgp']],
        ["Nome", dados['nome']],
        ["Vulgo", dados['vulgo']],
        ["RG/CPF", dados['rgcpf']],
        ["SSP", dados['ssp']],
        ["Nascimento", dados['nascimento']],
        ["Natureza", dados['natureza']],
        ["Data do Fato", dados['datafato']],
        ["BOPM-e", dados['bopme']],
        ["Equipe", dados['equipe']],
        ["Cidade", dados['cidade']],
        ["Endereço", dados['endereco']]
    ]

    # Criando a tabela e definindo o estilo
    table = Table(data, colWidths=[2.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    Story.append(table)
    Story.append(Paragraph(" ", styles["Normal"]))

    # Adicionar a foto, se disponível
    if foto_url:
        try:
            # Construir o caminho absoluto para a imagem
            img_path = os.path.join(app.root_path, foto_url[1:])

            # Decodificar espaços no nome do arquivo (se necessário) - descomente se precisar
            # img_path = img_path.replace('%20', ' ')

            print(f"Tentando abrir imagem em: {img_path}")
            img = Image(img_path, 4*inch, 4*inch, kind='proportional')
            Story.append(img)
        except Exception as e:
            print(f"Erro ao adicionar imagem: {e}")
            Story.append(Paragraph(f"Erro ao adicionar imagem: {e}", styles["Normal"]))

    # Construir o PDF
    doc.build(Story)

@app.route("/")
def inicial():
    return render_template("inicial.html")

@app.route('/qualificacao', methods=['GET'])
def qualificacao():
    dados = {
        'batalhao': request.args.get('batalhao'),
        'cia': request.args.get('cia'),
        'pelgp': request.args.get('pelgp'),
        'nome': request.args.get('nome'),
        'vulgo': request.args.get('vulgo'),
        'rgcpf': request.args.get('rgcpf'),
        'ssp': request.args.get('ssp'),
        'nascimento': request.args.get('nascimento'),
        'natureza': request.args.get('natureza'),
        'datafato': request.args.get('datafato'),
        'bopme': request.args.get('bopme'),
        'equipe': request.args.get('equipe'),
        'foto_url': request.args.get('foto_url'),
        'cidade': request.args.get('cidade'),
        'endereco': request.args.get('endereco')
    }
    try:
        pdf_filename = f"{dados['nome']}.pdf"
        pdf_filepath = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        generate_pdf(dados, pdf_filepath, dados.get('foto_url'))
        flash('PDF gerado com sucesso!')
    except Exception as e:
        flash(f'Erro ao gerar o PDF: {e}')
        print(f"Erro ao gerar o PDF: {e}")

    return render_template('qualificacao.html', **dados)

@app.route('/resultado', methods=['POST'])
def resultado():
    dados = {
        'batalhao': request.form.get('batalhao'),
        'cia': request.form.get('cia'),
        'pelgp': request.form.get('pelgp'),
        'nome': request.form.get('nome'),
        'vulgo': request.form.get('vulgo'),
        'rgcpf': request.form.get('rgcpf'),
        'ssp': request.form.get('ssp'),
        'nascimento': request.form.get('nascimento'),
        'natureza': request.form.get('natureza'),
        'datafato': request.form.get('datafato'),
        'bopme': request.form.get('bopme'),
        'equipe': request.form.get('equipe'),
        'cidade': request.form.get('cidade'),
        'endereco': request.form.get('endereco')
    }

   # Upload da foto
    foto = request.files.get('foto')
    foto_url = None
    if foto and foto.filename != '':
        filename = os.path.basename(foto.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        foto.save(file_path)
        foto_url = url_for('static', filename=f'uploads/{filename}')

    # Geração do PDF
    try:
        pdf_filename = f"{dados['nome']}.pdf"
        pdf_filepath = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        generate_pdf(dados, pdf_filepath, foto_url)
        flash('PDF gerado com sucesso!')
    except Exception as e:
        flash(f'Erro ao gerar o PDF: {e}')
        print(f"Erro ao gerar o PDF: {e}")

    return render_template('resultado.html', nome=dados['nome'], batalhao=dados['batalhao'], cia=dados['cia'], pelgp=dados['pelgp'], vulgo=dados['vulgo'], rgcpf=dados['rgcpf'], ssp=dados['ssp'], nascimento=dados['nascimento'], natureza=dados['natureza'], datafato=dados['datafato'], bopme=dados['bopme'], cidade=dados['cidade'], endereco=dados['endereco'], equipe=dados['equipe'], foto_url=foto_url)

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    print("Rota /upload-pdf acessada!")
    if 'pdf_file' not in request.files:
        flash('Nenhum arquivo PDF selecionado.')
        return redirect(url_for('inicial'))

    pdf_file = request.files['pdf_file']

    if pdf_file.filename == '':
        flash('Nenhum arquivo PDF selecionado.')
        return redirect(url_for('inicial'))

    if pdf_file and allowed_file(pdf_file.filename):
        filename = secure_filename(pdf_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pdf_file.save(filepath)

        flash('PDF salvo localmente com sucesso!')

        return redirect(url_for('inicial'))

    else:
        flash('Tipo de arquivo inválido. Envie um PDF.')
        return redirect(url_for('inicial'))

@app.route('/editar_qualificado', methods=['GET', 'POST'])
def editar_qualificado():
    if request.method == 'GET':
        dados = {
            'batalhao': request.args.get('batalhao'),
            'cia': request.args.get('cia'),
            'pelgp': request.args.get('pelgp'),
            'nome': request.args.get('nome'),
            'vulgo': request.args.get('vulgo'),
            'rgcpf': request.args.get('rgcpf'),
            'ssp': request.args.get('ssp'),
            'nascimento': request.args.get('nascimento'),
            'natureza': request.args.get('natureza'),
            'datafato': request.args.get('datafato'),
            'bopme': request.args.get('bopme'),
            'equipe': request.args.get('equipe'),
            'foto_url': request.args.get('foto_url'),
            'cidade': request.args.get('cidade'),
            'endereco': request.args.get('endereco')
        }
        return render_template('editar_qualificado.html', **dados)

    if request.method == 'POST':
        dados = {
            'batalhao': request.form.get('batalhao'),
            'cia': request.form.get('cia'),
            'pelgp': request.form.get('pelgp'),
            'nome': request.form.get('nome'),
            'vulgo': request.form.get('vulgo'),
            'rgcpf': request.form.get('rgcpf'),
            'ssp': request.form.get('ssp'),
            'nascimento': request.form.get('nascimento'),
            'natureza': request.form.get('natureza'),
            'datafato': request.form.get('datafato'),
            'bopme': request.form.get('bopme'),
            'equipe': request.form.get('equipe'),
            'cidade': request.form.get('cidade'),
            'endereco': request.form.get('endereco')
        }

        foto = request.files.get('foto')
        foto_url = request.form.get('foto_url')

        if foto and foto.filename != '':
            filename = os.path.basename(foto.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(file_path)
            foto_url = url_for('static', filename=f'uploads/{filename}')

        return render_template('resultado.html', nome=dados['nome'], batalhao=dados['batalhao'], cia=dados['cia'], pelgp=dados['pelgp'], vulgo=dados['vulgo'], rgcpf=dados['rgcpf'], ssp=dados['ssp'], nascimento=dados['nascimento'], natureza=dados['natureza'], datafato=dados['datafato'], bopme=dados['bopme'], cidade=dados['cidade'], endereco=dados['endereco'], equipe=dados['equipe'], foto_url=foto_url)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "Arquivo não encontrado", 404

@app.route('/informacao')
def informacao():
    return render_template('informacao.html')

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)