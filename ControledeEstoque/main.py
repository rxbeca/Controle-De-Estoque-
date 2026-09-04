import sys
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, 
    QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Controle de Estoque")
        self.resize(900, 500)

        # Widget central e layout principal
        self.widget_central = QWidget()
        self.setCentralWidget(self.widget_central)
        self.layout_principal = QVBoxLayout(self.widget_central)

        # Layout dos botões de ação superior
        self.layout_botoes = QHBoxLayout()
        
        self.btn_atualizar = QPushButton("Atualizar Lista")
        self.btn_atualizar.clicked.connect(self.carregar_produtos)
        self.layout_botoes.addWidget(self.btn_atualizar)

        self.btn_novo_produto = QPushButton("+ Novo Produto")
        # self.btn_novo_produto.clicked.connect(self.abrir_cadastro_produto) -> Implementaremos em breve
        self.layout_botoes.addWidget(self.btn_novo_produto)

        self.btn_movimentacao = QPushButton("Registrar Movimentação")
        # self.btn_movimentacao.clicked.connect(self.abrir_movimentacao) -> Implementaremos em breve
        self.layout_botoes.addWidget(self.btn_movimentacao)

        self.layout_principal.addLayout(self.layout_botoes)

        # Tabela de Produtos
        self.tabela_produtos = QTableWidget()
        self.tabela_produtos.setColumnCount(7)
        self.tabela_produtos.setHorizontalHeaderLabels([
            "ID", "Nome", "SKU", "Categoria", "Preço Custo", "Preço Venda", "Qtd. Atual"
        ])
        # Ajustar colunas para preencher a tela
        self.tabela_produtos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout_principal.addWidget(self.tabela_produtos)

        # Carregar os dados ao iniciar
        self.carregar_produtos()

    def carregar_produtos(self):
        """Busca os produtos no banco de dados SQLite e preenche a tabela."""
        self.tabela_produtos.setRowCount(0)
        try:
            conexao = sqlite3.connect("estoque.db")
            cursor = conexao.cursor()
            
            # Consulta unindo produtos com categorias para trazer o nome da categoria
            query = """
                SELECT p.id, p.nome, p.sku, c.nome, p.preco_custo, p.preco_venda, p.quantidade_atual
                FROM produtos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
            """
            cursor.execute(query)
            produtos = cursor.fetchall()
            conexao.close()

            self.tabela_produtos.setRowCount(len(produtos))
            for linha_idx, produto in enumerate(produtos):
                for coluna_idx, valor in enumerate(produto):
                    # Formatar valores se necessário (ex: preço)
                    item_str = str(valor) if valor is not None else ""
                    if coluna_idx in (4, 5) and valor is not None:
                        item_str = f"R$ {valor:.2f}"
                    
                    item = QTableWidgetItem(item_str)
                    # Alinhar números à direita
                    if coluna_idx >= 4:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
                    self.tabela_produtos.setItem(linha_idx, coluna_idx, item)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar produtos:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())