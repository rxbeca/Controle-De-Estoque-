import sys
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, 
    QMessageBox, QHeaderView, QDialog, QFormLayout, 
    QLineEdit, QSpinBox, QComboBox, QTextEdit, QTabWidget, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from database import (
    criar_banco, registrar_movimentacao_db, adicionar_item_ao_armario,
    verificar_credenciais, criar_usuario, gerar_token_redefinicao, redefinir_senha,
    excluir_item_db
)


def is_strong_password(password: str) -> tuple[bool, str]:
    if not password or len(password) < 8:
        return False, "A senha deve ter no mínimo 8 caracteres."
    if not any(c.isalpha() for c in password):
        return False, "A senha deve conter pelo menos uma letra."
    if not any(c.isdigit() for c in password):
        return False, "A senha deve conter pelo menos um número."
    return True, ""


class DialogNovoItem(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar Novo Item na CENDE")
        self.resize(400, 420)

        layout = QFormLayout(self)

        self.input_nome = QLineEdit()
        self.input_descricao = QTextEdit()
        self.input_descricao.setMaximumHeight(60)
        
        self.input_qtd = QSpinBox()
        self.input_qtd.setRange(0, 99999)

        self.input_patrimonio = QLineEdit()
        self.input_plaqueta = QLineEdit()
        self.input_local = QLineEdit()
        self.input_local.setPlaceholderText("Ex: Sala 04, Bloco B, Universidade...")

        self.combo_status = QComboBox()
        self.combo_status.addItems(["DISPONIVEL", "EM_USO", "MANUTENCAO", "INDISPONIVEL"])

        self.combo_armario = QComboBox()

        self.carregar_combos()

        layout.addRow("Nome do Item *:", self.input_nome)
        layout.addRow("Descrição:", self.input_descricao)
        layout.addRow("Quantidade Inicial:", self.input_qtd)
        layout.addRow("Patrimônio Pertencente:", self.input_patrimonio)
        layout.addRow("Nº Protocolo / Plaqueta:", self.input_plaqueta)
        layout.addRow("Local na Universidade:", self.input_local)
        layout.addRow("Status:", self.combo_status)
        layout.addRow("Guardar no Armário (Opcional):", self.combo_armario)

        self.btn_salvar = QPushButton("Cadastrar Item")
        self.btn_salvar.clicked.connect(self.salvar_item)
        layout.addRow(self.btn_salvar)

    def carregar_combos(self):
        conexao = sqlite3.connect("estoque.db")
        cursor = conexao.cursor()

        # Opção padrão para não vincular a nenhum armário
        self.combo_armario.addItem("Itens de Bens da CENDE", None)

        cursor.execute("SELECT id, nome FROM armarios")
        for arm_id, nome in cursor.fetchall():
            self.combo_armario.addItem(nome, arm_id)

        conexao.close()

    def salvar_item(self):
        nome = self.input_nome.text().strip()
        descricao = self.input_descricao.toPlainText().strip()
        qtd = self.input_qtd.value()
        patrimonio = self.input_patrimonio.text().strip()
        plaqueta = self.input_plaqueta.text().strip()
        local = self.input_local.text().strip()
        status = self.combo_status.currentText()
        # Pega o ID/Nome do armário selecionado
        armario_id = self.combo_armario.currentData()
        nome_armario = self.combo_armario.currentText() if armario_id is not None else None

        if not nome:
            QMessageBox.warning(self, "Atenção", "O nome do item é obrigatório!")
            return

        try:
            conexao = sqlite3.connect("estoque.db")
            cursor = conexao.cursor()
            
            cursor.execute("""
                INSERT INTO itens_cende (nome, descricao, quantidade_atual, patrimonio_pertence,
                                        numero_protocolo_plaqueta, local, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nome, descricao, qtd, patrimonio, plaqueta, local, status))
            
            conexao.commit()
            conexao.close()

            # Só adiciona no armário se um armário válido tiver sido escolhido
            if nome_armario:
                adicionar_item_ao_armario(nome_armario, nome)

            QMessageBox.information(self, "Sucesso", "Item cadastrado com sucesso!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar no banco: {e}")


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setFixedSize(1000, 600)

        main_layout = QVBoxLayout(self)

        self.logo_label = QLabel()
        self.logo_label.setFixedHeight(220)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("border: 1px solid #ccc; background: #f7f7f7;")
        
        try:
            pix = QPixmap("logo.png")
            if not pix.isNull():
                self.logo_label.setPixmap(pix.scaledToHeight(200, Qt.SmoothTransformation))
            else:
                self.logo_label.setText("LOGO AQUI")
        except Exception:
            self.logo_label.setText("LOGO AQUI")

        main_layout.addWidget(self.logo_label)

        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        form_widget = QWidget()
        form_widget.setFixedWidth(420)
        form_layout = QFormLayout(form_widget)

        self.input_username = QLineEdit()
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Usuário:", self.input_username)
        form_layout.addRow("Senha:", self.input_password)

        btns_layout = QHBoxLayout()
        self.btn_login = QPushButton("Entrar")
        self.btn_cadastrar = QPushButton("Cadastrar novo usuário")
        self.btn_esqueceu = QPushButton("Esqueceu a senha?")

        self.btn_login.clicked.connect(self.tentar_login)
        self.btn_cadastrar.clicked.connect(self.abrir_cadastro)
        self.btn_esqueceu.clicked.connect(self.abrir_esqueci)

        btns_layout.addWidget(self.btn_login)
        btns_layout.addWidget(self.btn_cadastrar)
        btns_layout.addWidget(self.btn_esqueceu)

        central_layout.addWidget(form_widget)
        central_layout.addLayout(btns_layout)

        main_layout.addWidget(central_widget)

    def tentar_login(self):
        username = self.input_username.text().strip()
        senha = self.input_password.text().strip()
        if not username or not senha:
            QMessageBox.warning(self, "Atenção", "Preencha usuário e senha.")
            return

        if verificar_credenciais(username, senha):
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Usuário ou senha inválidos.")

    def abrir_cadastro(self):
        dialog = DialogCadastroUsuario(self)
        dialog.exec()

    def abrir_esqueci(self):
        dialog = DialogEsqueciSenha(self)
        dialog.exec()


class DialogCadastroUsuario(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar Usuário")
        self.setFixedSize(360, 220)
        layout = QFormLayout(self)

        self.input_username = QLineEdit()
        self.input_email = QLineEdit()
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password2 = QLineEdit()
        self.input_password2.setEchoMode(QLineEdit.Password)

        layout.addRow("Usuário:", self.input_username)
        layout.addRow("Email:", self.input_email)
        layout.addRow("Senha:", self.input_password)
        layout.addRow("Confirmar senha:", self.input_password2)

        self.btn_salvar = QPushButton("Cadastrar")
        self.btn_salvar.clicked.connect(self.cadastrar)
        layout.addRow(self.btn_salvar)

    def cadastrar(self):
        user = self.input_username.text().strip()
        email = self.input_email.text().strip()
        p1 = self.input_password.text()
        p2 = self.input_password2.text()

        if not user or not email or not p1:
            QMessageBox.warning(self, "Atenção", "Preencha todos os campos.")
            return
        if p1 != p2:
            QMessageBox.warning(self, "Atenção", "Senhas não conferem.")
            return
        ok_pw, msg_pw = is_strong_password(p1)
        if not ok_pw:
            QMessageBox.warning(self, "Senha fraca", msg_pw)
            return

        ok, msg = criar_usuario(user, email, p1)
        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", msg)


class DialogEsqueciSenha(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recuperar Senha (Local)")
        self.setFixedSize(360, 140)
        layout = QFormLayout(self)

        self.input_email = QLineEdit()
        layout.addRow("Email cadastrado:", self.input_email)

        self.btn_enviar = QPushButton("Gerar token de redefinição")
        self.btn_enviar.clicked.connect(self.enviar_link)
        layout.addRow(self.btn_enviar)

    def enviar_link(self):
        email = self.input_email.text().strip()
        if not email:
            QMessageBox.warning(self, "Atenção", "Informe o email cadastrado.")
            return

        ok, token_or_msg = gerar_token_redefinicao(email)
        if not ok:
            QMessageBox.critical(self, "Erro", token_or_msg)
            return
        token = token_or_msg

        QMessageBox.information(self, "Token gerado",
                                "Token de redefinição gerado. Você pode redefinir a senha localmente a seguir.")
        dlg = DialogRedefinirSenha(token, self)
        dlg.exec()
        self.accept()


class DialogRedefinirSenha(QDialog):
    def __init__(self, token=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Redefinir Senha (Local)")
        self.setFixedSize(420, 200)

        layout = QFormLayout(self)
        self.input_token = QLineEdit()
        if token:
            self.input_token.setText(token)
        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.Password)
        self.input_senha2 = QLineEdit()
        self.input_senha2.setEchoMode(QLineEdit.Password)

        layout.addRow("Token:", self.input_token)
        layout.addRow("Nova senha:", self.input_senha)
        layout.addRow("Confirmar senha:", self.input_senha2)

        self.btn_redefinir = QPushButton("Redefinir senha")
        self.btn_redefinir.clicked.connect(self.redefinir)
        layout.addRow(self.btn_redefinir)

    def redefinir(self):
        token = self.input_token.text().strip()
        p1 = self.input_senha.text()
        p2 = self.input_senha2.text()

        if not token or not p1:
            QMessageBox.warning(self, "Atenção", "Preencha o token e a nova senha.")
            return
        if p1 != p2:
            QMessageBox.warning(self, "Atenção", "Senhas não conferem.")
            return

        ok_pw, msg_pw = is_strong_password(p1)
        if not ok_pw:
            QMessageBox.warning(self, "Senha fraca", msg_pw)
            return

        ok, msg = redefinir_senha(token, p1)
        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", msg)


class DialogMovimentacao(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Movimentação de Estoque")
        self.setFixedSize(400, 250)

        layout = QFormLayout(self)

        self.combo_item = QComboBox()
        self.combo_tipo = QComboBox()
        self.input_qtd = QSpinBox()
        self.input_qtd.setRange(1, 99999)
        self.input_obs = QTextEdit()
        self.input_obs.setMaximumHeight(60)

        self.carregar_dados()

        layout.addRow("Item da CENDE:", self.combo_item)
        layout.addRow("Tipo Movimentação:", self.combo_tipo)
        layout.addRow("Quantidade:", self.input_qtd)
        layout.addRow("Observação:", self.input_obs)

        self.btn_salvar = QPushButton("Confirmar Movimentação")
        self.btn_salvar.clicked.connect(self.salvar_movimentacao)
        layout.addRow(self.btn_salvar)

    def carregar_dados(self):
        conexao = sqlite3.connect("estoque.db")
        cursor = conexao.cursor()

        cursor.execute("SELECT id, nome, quantidade_atual FROM itens_cende")
        for i_id, nome, qtd in cursor.fetchall():
            self.combo_item.addItem(f"{nome} (Qtd atual: {qtd})", i_id)

        cursor.execute("SELECT id, nome, tipo FROM tipos_movimentacao")
        for t_id, nome, tipo in cursor.fetchall():
            self.combo_tipo.addItem(f"[{tipo}] {nome}", t_id)

        conexao.close()

    def salvar_movimentacao(self):
        item_id = self.combo_item.currentData()
        tipo_id = self.combo_tipo.currentData()
        quantidade = self.input_qtd.value()
        observacao = self.input_obs.toPlainText().strip()

        if not item_id or not tipo_id:
            QMessageBox.warning(self, "Atenção", "Selecione o item e o tipo de movimentação.")
            return

        sucesso, msg = registrar_movimentacao_db(item_id, tipo_id, quantidade, observacao)
        if sucesso:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", f"Falha na operação: {msg}")


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Controle de Estoque - CENDE")
        self.resize(1000, 600)

        self.widget_central = QWidget()
        self.setCentralWidget(self.widget_central)
        self.layout_principal = QVBoxLayout(self.widget_central)

        # Barra Superior de Botões
        self.layout_botoes = QHBoxLayout()
        
        self.btn_atualizar = QPushButton("Atualizar Dados")
        self.btn_atualizar.clicked.connect(self.atualizar_tudo)
        self.layout_botoes.addWidget(self.btn_atualizar)

        self.btn_novo_item = QPushButton("+ Novo Item")
        self.btn_novo_item.clicked.connect(self.abrir_cadastro_item)
        self.layout_botoes.addWidget(self.btn_novo_item)

        self.btn_movimentacao = QPushButton("Registrar Movimentação")
        self.btn_movimentacao.clicked.connect(self.abrir_movimentacao)
        self.layout_botoes.addWidget(self.btn_movimentacao)

        self.btn_excluir_item = QPushButton("Excluir Item")
        self.btn_excluir_item.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold;")
        self.btn_excluir_item.clicked.connect(self.excluir_item_selecionado)
        self.layout_botoes.addWidget(self.btn_excluir_item)

        self.btn_sair = QPushButton("Sair")
        self.btn_sair.clicked.connect(self.logout)
        self.layout_botoes.addWidget(self.btn_sair)

        self.layout_principal.addLayout(self.layout_botoes)

        # Abas
        self.abas = QTabWidget()
        
        # Aba 1: Itens da CENDE
        self.aba_itens = QWidget()
        self.layout_aba_itens = QVBoxLayout(self.aba_itens)

        self.input_pesquisa_item = QLineEdit()
        self.input_pesquisa_item.setPlaceholderText("Pesquisar item pelo nome...")
        self.input_pesquisa_item.textChanged.connect(self.filtrar_itens)
        self.layout_aba_itens.addWidget(self.input_pesquisa_item)

        self.tabela_itens = QTableWidget()
        self.tabela_itens.setColumnCount(8)
        self.tabela_itens.setHorizontalHeaderLabels([
            "ID", "Nome", "Descrição", "Qtd", "Patrimônio", "Plaqueta", "Local", "Status"
        ])
        self.tabela_itens.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_itens.setSelectionBehavior(QTableWidget.SelectRows)
        self.layout_aba_itens.addWidget(self.tabela_itens)
        self.abas.addTab(self.aba_itens, "Itens da CENDE")

        # Aba 2: Controle de Armários
        self.aba_armarios = QWidget()
        self.layout_aba_armarios = QVBoxLayout(self.aba_armarios)
        
        layout_filtro_armario = QHBoxLayout()
        layout_filtro_armario.addWidget(QLabel("Selecionar Armário:"))
        self.combo_filtro_armario = QComboBox()
        self.combo_filtro_armario.currentIndexChanged.connect(self.carregar_itens_armario)
        layout_filtro_armario.addWidget(self.combo_filtro_armario)
        layout_filtro_armario.addStretch()

        self.tabela_armarios = QTableWidget()
        self.tabela_armarios.setColumnCount(1)
        self.tabela_armarios.setHorizontalHeaderLabels(["Nome dos Itens Presentes neste Armário"])
        self.tabela_armarios.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.layout_aba_armarios.addLayout(layout_filtro_armario)
        self.layout_aba_armarios.addWidget(self.tabela_armarios)
        self.abas.addTab(self.aba_armarios, "Visualizar por Armário")

        self.layout_principal.addWidget(self.abas)

        self.carregar_armarios_combo()
        self.atualizar_tudo()

    def atualizar_tudo(self):
        self.carregar_itens_cende()
        self.carregar_itens_armario()

    def carregar_itens_cende(self):
        self.tabela_itens.setRowCount(0)
        try:
            conexao = sqlite3.connect("estoque.db")
            cursor = conexao.cursor()
            
            query = """
                SELECT id, nome, descricao, quantidade_atual,
                       patrimonio_pertence, numero_protocolo_plaqueta,
                       local, status
                FROM itens_cende
            """
            cursor.execute(query)
            itens = cursor.fetchall()
            conexao.close()

            self.tabela_itens.setRowCount(len(itens))
            for linha_idx, item in enumerate(itens):
                for coluna_idx, valor in enumerate(item):
                    item_str = str(valor) if valor is not None else ""
                    widget_item = QTableWidgetItem(item_str)
                    if coluna_idx in (0, 3):
                        widget_item.setTextAlignment(Qt.AlignCenter)
                    self.tabela_itens.setItem(linha_idx, coluna_idx, widget_item)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar itens:\n{e}")

    def filtrar_itens(self, texto):
        """Exibe somente as linhas cujo nome contém o texto pesquisado."""
        texto = texto.strip().casefold()

        for linha in range(self.tabela_itens.rowCount()):
            item_nome = self.tabela_itens.item(linha, 1)
            nome = item_nome.text().casefold() if item_nome else ""
            self.tabela_itens.setRowHidden(linha, texto not in nome)

    def carregar_armarios_combo(self):
        self.combo_filtro_armario.clear()
        conexao = sqlite3.connect("estoque.db")
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome FROM armarios")
        for a_id, nome in cursor.fetchall():
            self.combo_filtro_armario.addItem(nome, a_id)
        conexao.close()

    def carregar_itens_armario(self):
        self.tabela_armarios.setRowCount(0)
        armario_id = self.combo_filtro_armario.currentData()
        if not armario_id:
            return

        conexao = sqlite3.connect("estoque.db")
        cursor = conexao.cursor()
        cursor.execute("SELECT nome_item FROM itens_armario WHERE armario_id = ?", (armario_id,))
        itens = cursor.fetchall()
        conexao.close()

        self.tabela_armarios.setRowCount(len(itens))
        for linha_idx, item in enumerate(itens):
            self.tabela_armarios.setItem(linha_idx, 0, QTableWidgetItem(item[0]))

    def abrir_cadastro_item(self):
        dialogo = DialogNovoItem(self)
        if dialogo.exec():
            self.atualizar_tudo()

    def abrir_movimentacao(self):
        dialogo = DialogMovimentacao(self)
        if dialogo.exec():
            self.atualizar_tudo()

    def excluir_item_selecionado(self):
        linha_selecionada = self.tabela_itens.currentRow()
        
        if linha_selecionada == -1:
            QMessageBox.warning(self, "Atenção", "Selecione uma linha na tabela para excluir.")
            return

        item_id = self.tabela_itens.item(linha_selecionada, 0).text()
        nome_item = self.tabela_itens.item(linha_selecionada, 1).text()

        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja excluir permanentemente o item '{nome_item}' (ID: {item_id})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if resposta == QMessageBox.Yes:
            sucesso, msg = excluir_item_db(int(item_id))
            if sucesso:
                QMessageBox.information(self, "Sucesso", msg)
                self.atualizar_tudo()
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir o item: {msg}")

    def logout(self):
        login = LoginDialog(self)
        self.hide()
        if login.exec() == QDialog.Accepted:
            self.show()
            self.atualizar_tudo()
        else:
            QApplication.quit()


if __name__ == "__main__":
    criar_banco()
    app = QApplication(sys.argv)

    login = LoginDialog()
    if login.exec() == QDialog.Accepted:
        janela = JanelaPrincipal()
        janela.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)
