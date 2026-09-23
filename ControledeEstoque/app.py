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
    excluir_item_armario,
    pesquisar_item
)

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura_cende'

criar_banco()


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


@app.route('/armarios')
def armarios_page():
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    armarios = listar_armarios_com_itens()
    return render_template('armarios.html', armarios=armarios, usuario=session['usuario'])


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

    inserir_item_cende(nome, descricao, patrimonio, plaqueta, local, status)
    return redirect(url_for('dashboard'))


@app.route('/item/excluir/<int:item_id>', methods=['POST'])
def excluir_item(item_id):
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    excluir_item_db(item_id)
    return redirect(url_for('dashboard'))


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

    edicao_de_itens(item_id, nome, descricao, patrimonio, plaqueta, local, status)
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

    sucesso, mensagem = atualizar_item_por_coluna(int(item_id), coluna, valor)
    if sucesso:
        return jsonify({'sucesso': True, 'mensagem': mensagem})
    return jsonify({'sucesso': False, 'mensagem': mensagem}), 400


@app.route('/armario/<int:armario_id>/item/novo', methods=['POST'])
def novo_item_armario(armario_id):
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    nome_item = request.form.get('nome_item', '').strip()
    if nome_item:
        inserir_item_armario(armario_id, nome_item)
    return redirect(url_for('armarios_page'))


@app.route('/armario/item/excluir/<int:item_id>', methods=['POST'])
def excluir_item_armario_rota(item_id):
    if 'usuario' not in session:
        return redirect(url_for('login_page'))

    excluir_item_armario(item_id)
    return redirect(url_for('armarios_page'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)