import sqlite3
import hashlib
import os
import binascii
from datetime import datetime, timedelta

def criar_banco():
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()

    # Tabela Principal dos Itens da CENDE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_cende (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            quantidade_atual INTEGER DEFAULT 0,
            patrimonio_pertence TEXT,
            numero_protocolo_plaqueta TEXT,
            local TEXT,
            status TEXT CHECK(status IN ('DISPONIVEL', 'EM_USO', 'MANUTENCAO', 'INDISPONIVEL')) DEFAULT 'DISPONIVEL'
        )
    """)

    # 3. Tabela de Armários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS armarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    # 4. Tabela de ligação: itens no armário
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

    # 6. Tabela de Movimentações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            tipo_movimentacao_id INTEGER,
            quantidade INTEGER NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            observacao TEXT,
            FOREIGN KEY (item_id) REFERENCES itens_cende(id) ON DELETE CASCADE,
            FOREIGN KEY (tipo_movimentacao_id) REFERENCES tipos_movimentacao(id)
        )
    """)

    # 7. Tabela de Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            reset_token TEXT,
            reset_expiry TIMESTAMP
        )
    """)

    # INSERÇÃO DE DADOS PADRÃO
    cursor.execute("SELECT COUNT(*) FROM itens_cende")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO itens_cende (nome) VALUES (?)", [("Item de bens da CENDE",)])

    cursor.execute("SELECT COUNT(*) FROM armarios")
    if cursor.fetchone()[0] == 0:
        armarios_iniciais = [
            ("Armário 1",), ("Armário 2",), ("Armário 3",),
            ("Armário A",), ("Armário B",), ("Armário C",)
        ]
        cursor.executemany("INSERT INTO armarios (nome) VALUES (?)", armarios_iniciais)

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
    if not nome_armario:
        return True, "Item cadastrado sem vínculo a armários."

    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT id FROM armarios WHERE nome = ?", (nome_armario,))
        resultado = cursor.fetchone()
        if not resultado:
            return False, f"Armário '{nome_armario}' não encontrado."

        armario_id = resultado[0]
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


def _hash_password(password: str, salt: bytes = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    return binascii.hexlify(salt).decode() + ':' + binascii.hexlify(dk).decode()


def _verify_password(stored_hash: str, password: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split(':')
        salt = binascii.unhexlify(salt_hex)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
        return binascii.hexlify(dk).decode() == hash_hex
    except Exception:
        return False


def criar_usuario(username: str, email: str, password: str):
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        password_hash = _hash_password(password)
        cursor.execute("INSERT INTO usuarios (username, email, password_hash) VALUES (?, ?, ?)",
                       (username, email, password_hash))
        conexao.commit()
        return True, "Usuário criado com sucesso"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()


def verificar_credenciais(username: str, password: str) -> bool:
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT password_hash FROM usuarios WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            return False
        return _verify_password(row[0], password)
    finally:
        conexao.close()


def get_user_by_email(email: str):
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT id, username, email FROM usuarios WHERE email = ?", (email,))
        return cursor.fetchone()
    finally:
        conexao.close()


def gerar_token_redefinicao(email: str) -> tuple[bool, str]:
    user = get_user_by_email(email)
    if not user:
        return False, "Email não cadastrado"

    token = binascii.hexlify(os.urandom(16)).decode()
    expiry = datetime.utcnow() + timedelta(hours=1)

    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("UPDATE usuarios SET reset_token = ?, reset_expiry = ? WHERE email = ?",
                       (token, expiry.isoformat(), email))
        conexao.commit()
        return True, token
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()


def redefinir_senha(token: str, nova_senha: str) -> tuple[bool, str]:
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT id, reset_expiry FROM usuarios WHERE reset_token = ?", (token,))
        row = cursor.fetchone()
        if not row:
            return False, "Token inválido"

        expiry = row[1]
        if expiry is None or datetime.fromisoformat(expiry) < datetime.utcnow():
            return False, "Token expirado"

        password_hash = _hash_password(nova_senha)
        cursor.execute("UPDATE usuarios SET password_hash = ?, reset_token = NULL, reset_expiry = NULL WHERE id = ?",
                       (password_hash, row[0]))
        conexao.commit()
        return True, "Senha redefinida com sucesso"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()


def listar_itens_do_armario(nome_armario):
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


def registrar_movimentacao_db(item_id, tipo_movimentacao_id, quantidade, observacao=""):
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT tipo FROM tipos_movimentacao WHERE id = ?", (tipo_movimentacao_id,))
        resultado = cursor.fetchone()
        if not resultado:
            raise ValueError("Tipo de movimentação inválido.")
        
        tipo = resultado[0]

        cursor.execute("""
            INSERT INTO movimentacoes (item_id, tipo_movimentacao_id, quantidade, observacao)
            VALUES (?, ?, ?, ?)
        """, (item_id, tipo_movimentacao_id, quantidade, observacao))

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


def excluir_item_db(item_id: int):
    """Remove um item da tabela itens_cende e seus registros associados."""
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT nome FROM itens_cende WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        
        if item:
            nome_item = item[0]
            cursor.execute("DELETE FROM itens_armario WHERE nome_item = ?", (nome_item,))

        cursor.execute("DELETE FROM movimentacoes WHERE item_id = ?", (item_id,))
        cursor.execute("DELETE FROM itens_cende WHERE id = ?", (item_id,))
        
        conexao.commit()
        return True, "Item excluído com sucesso!"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()


if __name__ == "__main__":
    criar_banco()
