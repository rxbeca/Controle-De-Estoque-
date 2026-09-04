import sqlite3

def criar_banco():
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()

    # 1. Tabela de Categorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)

    # 2. Tabela Principal dos Itens da CENDE (com todas as informações detalhadas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_cende (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            quantidade_atual INTEGER DEFAULT 0,
            patrimonio_pertence TEXT,
            numero_protocolo_plaqueta TEXT,
            local TEXT,
            status TEXT CHECK(status IN ('DISPONIVEL', 'EM_USO', 'MANUTENCAO', 'BAIXADO')) DEFAULT 'DISPONIVEL',
            categoria_id INTEGER,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)
    # 3. Tabela de Armários (locais específicos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS armarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    # 4. Tabela de ligação: guarda APENAS o nome do item vinculado ao armário
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_armario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            armario_id INTEGER NOT NULL,
            nome_item TEXT NOT NULL,
            FOREIGN KEY (armario_id) REFERENCES armarios(id)
        )
    """)

    # 5. Tabela de Tipos de Movimentação
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_movimentacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT CHECK(tipo IN ('ENTRADA', 'SAIDA')) NOT NULL
        )
    """)

    # 6. Tabela de Movimentações (Histórico)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            tipo_movimentacao_id INTEGER,
            quantidade INTEGER NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            observacao TEXT,
            FOREIGN KEY (item_id) REFERENCES itens_cende(id),
            FOREIGN KEY (tipo_movimentacao_id) REFERENCES tipos_movimentacao(id)
        )
    """)

    # --- INSERÇÃO DE DADOS PADRÃO ---

    # Cadastra os armários se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM armarios")
    if cursor.fetchone()[0] == 0:
        armarios_iniciais = [
            ("Armário 1",),
            ("Armário 2",),
            ("Armário 3",),
            ("Armário A",),
            ("Armário B",),
            ("Armário C",)
        ]
        cursor.executemany("INSERT INTO armarios (nome) VALUES (?)", armarios_iniciais)

    # Cadastra os tipos de movimentação se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM tipos_movimentacao")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO tipos_movimentacao (nome, tipo) VALUES (?, ?)", [
            ("Entrada / Cadastro", "ENTRADA"),
            ("Saída / Empréstimo", "SAIDA"),
            ("Devolução", "ENTRADA"),
            ("Ajuste de Inventário (Positivo)", "ENTRADA"),
            ("Ajuste de Inventário (Negativo)", "SAIDA")
        ])

    conexao.commit()
    conexao.close()
    print("Banco de dados criado com sucesso!")


def adicionar_item_ao_armario(nome_armario, nome_item):
    """
    Função auxiliar para adicionar apenas o nome de um item dentro de um armário específico.
    """
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()

    try:
        # Busca o ID do armário pelo nome (ex: 'Armário 1')
        cursor.execute("SELECT id FROM armarios WHERE nome = ?", (nome_armario,))
        resultado = cursor.fetchone()

        if not resultado:
            return False, f"Armário '{nome_armario}' não encontrado."

        armario_id = resultado[0]

        # Insere o nome do item associado ao armário
        cursor.execute("""
            INSERT INTO itens_armario (armario_id, nome_item)
            VALUES (?, ?)
        """, (armario_id, nome_item))

        conexao.commit()
        return True, f"Item '{nome_item}' adicionado ao {nome_armario} com sucesso!"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()


def listar_itens_do_armario(nome_armario):
    """
    Função auxiliar para listar todos os nomes de itens armazenados em um determinado armário.
    """
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT ia.nome_item 
        FROM itens_armario ia
        JOIN armarios a ON ia.armario_id = a.id
        WHERE a.nome = ?
    """, (nome_armario,))

    itens = cursor.fetchall()
    conexao.close()
    return [item[0] for item in itens]


if __name__ == "__main__":
    criar_banco()
# ... (Mantenha a função criar_banco aqui) ...

def registrar_movimentacao_db(item_id, tipo_movimentacao_id, quantidade, observacao=""):
    """
    Registra uma movimentação no histórico e atualiza a quantidade do item na tabela itens_cende.
    """
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()

    try:
        # 1. Buscar o tipo da movimentação (ENTRADA ou SAIDA)
        cursor.execute("SELECT tipo FROM tipos_movimentacao WHERE id = ?", (tipo_movimentacao_id,))
        resultado = cursor.fetchone()
        if not resultado:
            raise ValueError("Tipo de movimentação inválido.")
        
        tipo = resultado[0]

        # 2. Registrar no histórico usando item_id
        cursor.execute("""
            INSERT INTO movimentacoes (item_id, tipo_movimentacao_id, quantidade, observacao)
            VALUES (?, ?, ?, ?)
        """, (item_id, tipo_movimentacao_id, quantidade, observacao))

        # 3. Atualizar a tabela itens_cende
        if tipo == 'ENTRADA':
            cursor.execute("""
                UPDATE itens_cende SET quantidade_atual = quantidade_atual + ? WHERE id = ?
            """, (quantidade, item_id))
        elif tipo == 'SAIDA':
            cursor.execute("""
                UPDATE itens_cende SET quantidade_atual = quantidade_atual - ? WHERE id = ?
            """, (quantidade, item_id))

        conexao.commit()
        return True, "Movimentação registrada com sucesso!"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()
        
    
