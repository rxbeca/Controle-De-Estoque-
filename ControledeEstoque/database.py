import sqlite3

def criar_banco():
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()

    # Tabela de Categorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)

    # Tabela de Produtos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Itens da CENDE(
          CREATE TABLE IF NOT EXISTS itens_cende (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            quantidade_atual INTEGER DEFAULT 0,
            patrimonio_pertence TEXT,
            numero_protocolo_plaqueta TEXT,
            categoria_id INTEGER,
            status TEXT CHECK(status IN ('DISPONIVEL', 'EM_USO', 'MANUTENCAO', 'BAIXADO')) DEFAULT 'DISPONIVEL',
     
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)

    # Tabela de Tipos de Movimentação
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_movimentacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
          
        )
    """)

    # Tabela de Movimentações (Histórico)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            tipo_movimentacao_id INTEGER,
            quantidade INTEGER NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            observacao TEXT,
            FOREIGN KEY (produto_id) REFERENCES produtos(id),
            FOREIGN KEY (tipo_movimentacao_id) REFERENCES tipos_movimentacao(id)
        )
    """)

    # Inserir alguns tipos padrão se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM tipos_movimentacao")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO tipos_movimentacao (nome, tipo) VALUES (?, ?)", [
            ("Compra de Fornecedor", "ENTRADA"),
            ("Venda", "SAIDA"),
            ("Ajuste de Inventário (Positivo)", "ENTRADA"),
            ("Ajuste de Inventário (Negativo)", "SAIDA")
        ])

    conexao.commit()
    conexao.close()
    print("Banco de dados criado com sucesso!")

if __name__ == "__main__":
    criar_banco()

# ... (Mantenha a função criar_banco aqui) ...

def registrar_movimentacao_db(produto_id, tipo_movimentacao_id, quantidade, observacao=""):
    """
    Registra uma movimentação no histórico e atualiza a quantidade_atual do produto.
    """
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()

    try:
        # 1. Identificar se o tipo de movimentação é ENTRADA ou SAIDA
        cursor.execute("SELECT tipo FROM tipos_movimentacao WHERE id = ?", (tipo_movimentacao_id,))
        resultado = cursor.fetchone()
        if not resultado:
            raise ValueError("Tipo de movimentação inválido.")
        
        tipo = resultado[0]

        # 2. Inserir o registro no histórico de movimentações
        cursor.execute("""
            INSERT INTO movimentacoes (produto_id, tipo_movimentacao_id, quantidade, observacao)
            VALUES (?, ?, ?, ?)
        """, (produto_id, tipo_movimentacao_id, quantidade, observacao))

        # 3. Atualizar o estoque do produto
        if tipo == 'ENTRADA':
            cursor.execute("""
                UPDATE produtos SET quantidade_atual = quantidade_atual + ? WHERE id = ?
            """, (quantidade, produto_id))
        elif tipo == 'SAIDA':
            cursor.execute("""
                UPDATE produtos SET quantidade_atual = quantidade_atual - ? WHERE id = ?
            """, (quantidade, produto_id))

        conexao.commit()
        return True, "Movimentação registrada com sucesso!"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()
    