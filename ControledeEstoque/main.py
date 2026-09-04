import sys
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, 
    QMessageBox, QHeaderView, QDialog, QFormLayout, 
    QLineEdit, QSpinBox, QComboBox, QTextEdit, QTabWidget, QLabel
)
from PySide6.QtCore import Qt
from database import criar_banco, registrar_movimentacao_db, adicionar_item_ao_armario


# --- DIÁLOGO PARA CADASTRAR UM NOVO ITEM ---
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
        self.combo_status.addItems(["DISPONIVEL", "EM_USO", "MANUTENCAO", "BAIXADO"])

        self.combo_categoria = QComboBox()
        self.combo_armario = QComboBox()

        self.carregar_combos()

        # Adicionar elementos ao layout
        layout.addRow("Nome do Item *:", self.input_nome)
        layout.addRow("Descrição:", self.input_descricao)
        layout.addRow("Quantidade Inicial:", self.input_qtd)
        layout.addRow("Patrimônio Pertencente:", self.input_patrimonio)
        layout.addRow("Nº Protocolo / Plaqueta:", self.input_plaqueta)
        layout.addRow("Local na Universidade:", self.input_local)
        layout.addRow("Status:", self.combo_status)
        layout.addRow("Categoria:", self.combo_categoria)
        layout.addRow("Guardar no Armário:", self.combo_armario)

        self.btn_salvar = QPushButton("Cadastrar Item")
        self.btn_salvar.clicked.connect(self.salvar_item)
        layout.addRow(self.btn_salvar)

    def carregar_combos(self):
        conexao = sqlite3.connect("estoque.db")
        cursor = conexao.cursor()

        # Carregar Categorias
        cursor.execute("SELECT id, nome FROM categorias")
        for cat_id, nome in cursor.fetchall():
            self.combo_categoria.addItem(nome, cat_id)

        # Carregar Armários
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
        categoria_id = self.combo_categoria.currentData()
        nome_armario = self.combo_armario.currentText()

        if not nome:
            QMessageBox.warning(self, "Atenção", "O nome do item é obrigatório!")
            return

        try:
            conexao = sqlite3.connect("estoque.db")
            cursor = conexao.cursor()
            
            cursor.execute("""
                INSERT INTO itens_cende (nome, descricao, quantidade_atual, patrimonio_pertence, 
                                        numero_protocolo_plaqueta, local, status, categoria_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome, descricao, qtd, patrimonio, plaqueta, local, status, categoria_id))
            
            conexao.commit()
            conexao.close()

            # Vincular o nome do item ao armário selecionado
            adicionar_item_ao_armario(nome_armario, nome)

            QMessageBox.information(self, "Sucesso", "Item cadastrado com sucesso!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar no banco: {e}")


# --- DIÁLOGO DE REGISTRO DE MOVIMENTAÇÃO ---
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

        # CORREÇÃO: Busca da tabela itens_cende em vez de produtos
        cursor.execute("SELECT id, nome, quantidade_atual FROM itens_cende")
        for i_id, nome, qtd in cursor.fetchall():
            self.combo_item.addItem(f"{nome} (Qtd atual: {qtd})", i_id)

        # Carregar Tipos de Movimentação
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

        # Chama a função atualizada do banco
        sucesso, msg = registrar_movimentacao_db(item_id, tipo_id, quantidade, observacao)
        if sucesso:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", f"Falha na operação: {msg}")
# --- JANELA PRINCIPAL COM ABAS ---
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

        self.layout_principal.addLayout(self.layout_botoes)

        # Sistema de Abas
        self.abas = QTabWidget()
        
        # Aba 1: Itens da CENDE
        self.aba_itens = QWidget()
        self.layout_aba_itens = QVBoxLayout(self.aba_itens)
        self.tabela_itens = QTableWidget()
        self.tabela_itens.setColumnCount(9)
        self.tabela_itens.setHorizontalHeaderLabels([
            "ID", "Nome", "Descrição", "Qtd", "Patrimônio", "Plaqueta", "Local", "Status", "Categoria"
        ])
        self.tabela_itens.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

        # Carregar dados iniciais
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
                SELECT i.id, i.nome, i.descricao, i.quantidade_atual, 
                       i.patrimonio_pertence, i.numero_protocolo_plaqueta, 
                       i.local, i.status, c.nome
                FROM itens_cende i
                LEFT JOIN categorias c ON i.categoria_id = c.id
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


if __name__ == "__main__":
    criar_banco()
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())
