# EXTENSOES E BIBLIOTECAS USADAS NO PROJETO


import os
from werkzeug.utils import secure_filename
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from database import (
    criar_banco,
    verificar_credenciais,
    listar_itens_cende,
    inserir_item_cende,
    edicao_de_itens,
    excluir_item_db,
    criar_usuario,
    atualizar_item_por_coluna,
    listar_armarios_com_itens,
    inserir_item_armario,
    atualizar_item_armario,
    excluir_item_armario,
    pesquisar_item,
    pesquisar_itens_relatorio,
)

#ESSA EH O ARQUIVO NA QUAL O SITE IRAR RODAR A PARTE DO FUNCIONAMENTO LÓGICO POR TRAS DOS DEFS SAO FEITS NO DATABASE.PY ONDE TODOS OS DADOS SERAM COLETADOS!

#onde eu vou colocar as imagens 
app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura_cende'
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'upload')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpeg', 'webp', 'jpg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# BANCO DE DADOS A QUAL TA CONECTADO 
def get_db_connection():
    conn = sqlite3.connect('estoque.db')
    conn.row_factory = sqlite3.Row
    return conn
#ONDE INCIA O BANCO DE DADOS 
criar_banco()
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ROTA DE LOGIN E CADASTRO 
@app.route('/')
def login_page():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    usuario = request.form.get('usuario')
    senha = request.form.get('senha')

    if verificar_credenciais(usuario, senha):
        session['usuario'] = usuario
        return redirect(url_for('dashboard'))
    return render_template('login.html', erro='Usuário ou senha incorretos!')


@app.route('/register', methods=['POST'])
def register():
    novo_usuario = request.form.get('novo_usuario')
    novo_email = request.form.get('novo_email')
    nova_senha = request.form.get('nova_senha')
    confirma_senha = request.form.get('confirma_senha')

    if not (novo_usuario and novo_email and nova_senha and confirma_senha):
        return render_template('login.html', erro='Preencha todos os campos para criar usuário.')

    if nova_senha != confirma_senha:
        return render_template('login.html', erro='Senhas não conferem.')

    sucesso, msg = criar_usuario(novo_usuario, novo_email, nova_senha)
    if sucesso:
        session['usuario'] = novo_usuario
        return redirect(url_for('dashboard'))
    return render_template('login.html', erro=msg)


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login_page'))

#PESQUISA DE ITENS
@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    busca = request.args.get('q', '').strip()
    itens = pesquisar_item(busca) if busca else listar_itens_cende()
    armarios = listar_armarios_com_itens()
    return render_template(
        'index.html',
        itens=itens,
        armarios=armarios,
        usuario=session['usuario'],
        busca=busca,
    )

#ARMARIOS 
@app.route('/armarios')
def armarios_page():
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    armarios = listar_armarios_com_itens()
    return render_template('armarios.html', armarios=armarios, usuario=session['usuario'])

#RELATORIOS (A MAIORIA DOS DEF SAO AUTOEXPLICATIVOS ENTAO N EH TAO DIFICIL DE ENCONTRAR OS COMANDOS CERTOS)
@app.route('/relatorio')
def relatorio():
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    busca = request.args.get('busca', '').strip()
    itens = pesquisar_itens_relatorio(busca)
    return render_template(
        'relatorio.html',
        busca=busca,
        itens=itens,
        usuario=session['usuario'],
    )

# CADASTRO DE NOVO ITEM 
@app.route('/item/novo', methods=['POST'])
def novo_item():
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    nome = request.form.get('nome')
    descricao = request.form.get('descricao')
    patrimonio = request.form.get('patrimonio')
    plaqueta = request.form.get('plaqueta')
    local = request.form.get('local')
    status = request.form.get('status')
    categoria = request.form.get('categoria', '').strip()
    if not categoria:
        return 'Categoria é obrigatória.', 400

    imagem = request.files.get('imagem')
    nome_imagem = None
    if imagem and imagem.filename and allowed_file(imagem.filename):
        nome_imagem = secure_filename(imagem.filename)
        imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))

    inserir_item_cende(nome, descricao, patrimonio, plaqueta, local, status, nome_imagem, categoria)
    return redirect(url_for('dashboard'))

#EXCLUIR ITENS
@app.route('/item/excluir/<int:item_id>', methods=['POST'])
def excluir_item(item_id):
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    excluir_item_db(item_id)
    return redirect(url_for('dashboard'))

#EDÇÃO DOS ITENS 
@app.route('/item/editar/<int:item_id>', methods=['POST'])
def editar_item(item_id):
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    nome = request.form.get('nome')
    descricao = request.form.get('descricao')
    patrimonio = request.form.get('patrimonio')
    plaqueta = request.form.get('plaqueta')
    local = request.form.get('local')
    status = request.form.get('status')
    categoria = request.form.get('categoria', '').strip()
    if not categoria:
        return 'Categoria é obrigatória.', 400
    imagem = request.files.get('imagem')

    nome_imagem = None
    if imagem and imagem.filename and allowed_file(imagem.filename):
        nome_imagem = secure_filename(imagem.filename)
        imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))

    edicao_de_itens(item_id, nome, descricao, patrimonio, plaqueta, local, status, nome_imagem, categoria=categoria)
    return redirect(url_for('dashboard'))

@app.route('/api/item/atualizar', methods=['POST'])
def atualizar_item_api():
    if 'usuario' not in session:
        return jsonify({'sucesso': False, 'mensagem': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    item_id = dados.get('id')
    coluna = dados.get('coluna')
    valor = dados.get('valor')

    if item_id is None or coluna is None or valor is None:
        return jsonify({'sucesso': False, 'mensagem': 'Dados incompletos.'}), 400
    if coluna == 'categoria' and not str(valor).strip():
        return jsonify({'sucesso': False, 'mensagem': 'Categoria é obrigatória.'}), 400

    sucesso, mensagem = atualizar_item_por_coluna(int(item_id), coluna, valor)
    if sucesso:
        return jsonify({'sucesso': True, 'mensagem': mensagem})
    return jsonify({'sucesso': False, 'mensagem': mensagem}), 400

#CADASTRO DE ITEM NOS ARMARIOS(COMO SAO PAGINAS DIFERENTES E LUGARES DIFERRENTES, ELES FORAM DIVIDIDOS ASSIM PARA SER MAIS FACIL DE SE LOCALIZAR)

@app.route('/armario/<int:armario_id>/item/novo', methods=['POST'])
def novo_item_armario(armario_id):
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    nome_item = request.form.get('nome_item', '').strip()
    patrimonio = request.form.get('patrimonio', '').strip()
    categoria = request.form.get('categoria', '').strip()
    if not categoria:
        return 'Categoria é obrigatória.', 400

    arquivo = request.files.get('imagem')
    nome_imagem = None
    if arquivo and arquivo.filename and allowed_file(arquivo.filename):
        nome_imagem = secure_filename(arquivo.filename)
        arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))

    if nome_item and patrimonio:
        inserir_item_armario(armario_id, nome_item, nome_imagem, patrimonio, categoria)
    return redirect(url_for('armarios_page'))

#EDITAR DENTRO DOS ARMARIOS (MESMO LÓGICA DO DE CIMA RAPAZIADA )


@app.route('/armario/item/editar/<int:item_id>', methods=['POST'])
def editar_item_armario_rota(item_id):
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    nome_item = request.form.get('nome_item', '').strip()
    patrimonio_item = request.form.get('patrimonio_item', '').strip()
    categoria = request.form.get('categoria', '').strip()
    if not categoria:
        return 'Categoria é obrigatória.', 400
    arquivo = request.files.get('imagem')
    nome_imagem = None
    if arquivo and arquivo.filename and allowed_file(arquivo.filename):
        nome_imagem = secure_filename(arquivo.filename)
        arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))

    sucesso, mensagem = atualizar_item_armario(item_id, nome_item, patrimonio_item, nome_imagem, categoria)
    if not sucesso:
        return redirect(url_for('armarios_page'))
    return redirect(url_for('armarios_page'))

#EXCLUIR ITENS DOS ARMARIOS

@app.route('/armario/item/excluir/<int:item_id>', methods=['POST'])
def excluir_item_armario_rota(item_id):
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    excluir_item_armario(item_id)
    return redirect(url_for('armarios_page'))


if __name__ == '__main__':
    app.run( host='0.0.0.0',debug=False, port=5001)