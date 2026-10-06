import sqlite3
import hashlib
import os
import binascii


def criar_banco():
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS itens_cende (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            patrimonio_pertence TEXT NOT NULL,
            numero_protocolo_plaqueta TEXT NOT NULL,
            local TEXT NOT NULL,
            status TEXT CHECK(status IN ('DISPONIVEL', 'EM_USO', 'MANUTENCAO', 'INDISPONIVEL')) DEFAULT 'DISPONIVEL',
            imagem TEXT
        )
        """
    )

    colunas_itens = {
        coluna[1] for coluna in cursor.execute("PRAGMA table_info(itens_cende)").fetchall()
    }
    if "imagem" not in colunas_itens:
        cursor.execute("ALTER TABLE itens_cende ADD COLUMN imagem TEXT")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS armarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            imagem TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS itens_armario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            armario_id INTEGER NOT NULL,
            nome_item TEXT NOT NULL,
            imagem TEXT,
            FOREIGN KEY (armario_id) REFERENCES armarios(id)
        )
        """
    )

    colunas_itens_armario = {
        coluna[1] for coluna in cursor.execute("PRAGMA table_info(itens_armario)").fetchall()
    }
    if "imagem" not in colunas_itens_armario:
        cursor.execute("ALTER TABLE itens_armario ADD COLUMN imagem TEXT")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        """
    )

    cursor.execute("SELECT COUNT(*) FROM armarios")
    if cursor.fetchone()[0] == 0:
        armarios_iniciais = [
            ("Armário 1",),
            ("Armário 2",),
            ("Armário 3",),
            ("Armário A",),
            ("Armário B",),
            ("Armário C",),
        ]
        cursor.executemany("INSERT INTO armarios (nome) VALUES (?)", armarios_iniciais)

    conexao.commit()
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


def criar_usuario(username: str, email: str, password: str):
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        password_hash = _hash_password(password)
        cursor.execute(
            "INSERT INTO usuarios (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        conexao.commit()
        return True, "Usuário criado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Nome de usuário ou email já existe."
    except Exception as e:
        return False, str(e)
    finally:
        conexao.close()


def listar_itens_cende():
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT id, nome, descricao, patrimonio_pertence, numero_protocolo_plaqueta, local, status, imagem FROM itens_cende"
    )
    itens = cursor.fetchall()
    conexao.close()
    return itens


def inserir_item_cende(nome, descricao, patrimonio, plaqueta, local, status, imagem=None):
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO itens_cende (nome, descricao, patrimonio_pertence, numero_protocolo_plaqueta, local, status, imagem)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (nome, descricao, patrimonio, plaqueta, local, status, imagem),
        )
        conexao.commit()
        return True, "Item cadastrado com sucesso!"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()


def atualizar_item_por_coluna(item_id: int, coluna: str, valor):
    colunas_permitidas = {
        "nome": "nome",
        "descricao": "descricao",
        "patrimonio": "patrimonio_pertence",
        "plaqueta": "numero_protocolo_plaqueta",
        "local": "local",
        "status": "status",
        "imagem": "imagem",
    }

    if coluna not in colunas_permitidas:
        return False, "Coluna inválida."

    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        query = f"UPDATE itens_cende SET {colunas_permitidas[coluna]} = ? WHERE id = ?"
        cursor.execute(query, (valor, item_id))
        conexao.commit()
        return True, "Atualizado com sucesso!"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()


def edicao_de_itens(item_id, nome, descricao, patrimonio, plaqueta, local, status, imagem):
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute(
            """
            UPDATE itens_cende
            SET nome = ?, descricao = ?, patrimonio_pertence = ?, numero_protocolo_plaqueta = ?, local = ?, status = ?, imagem = COALESCE(?, imagem)
            WHERE id = ?
            """,
            (nome, descricao, patrimonio, plaqueta, local, status, imagem, item_id),
        )
        conexao.commit()
        return True, "Item atualizado com sucesso!"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()


def excluir_item_db(item_id: int):
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("DELETE FROM itens_cende WHERE id = ?", (item_id,))
        conexao.commit()
        return True, "Item excluído com sucesso!"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()


def listar_armarios_com_itens():
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT a.id, a.nome, ia.id, ia.nome_item, ia.imagem
        FROM armarios AS a
        LEFT JOIN itens_armario AS ia ON ia.armario_id = a.id
        ORDER BY a.id, ia.id
        """
    )

    armarios = {}
    for armario_id, nome, item_id, nome_item, imagem in cursor.fetchall():
        if armario_id not in armarios:
            armarios[armario_id] = {"id": armario_id, "nome": nome, "itens": []}
        if item_id is not None:
            armarios[armario_id]["itens"].append(
                {"id": item_id, "nome": nome_item, "imagem": imagem}
            )

    conexao.close()
    return list(armarios.values())


def inserir_item_armario(armario_id: int, nome_item: str, imagem=None):
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT id FROM armarios WHERE id = ?", (armario_id,))
        if cursor.fetchone() is None:
            return False, "Armário não encontrado."

        cursor.execute(
            "INSERT INTO itens_armario (armario_id, nome_item, imagem) VALUES (?, ?, ?)",
            (armario_id, nome_item, imagem),
        )
        conexao.commit()
        return True, "Item adicionado ao armário."
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()


def excluir_item_armario(item_id: int):
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("DELETE FROM itens_armario WHERE id = ?", (item_id,))
        conexao.commit()
        return True, "Item removido do armário."
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()

def pesquisar_item(termo):
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    padrao = f"%{termo}%"
    cursor.execute(
        """
         SELECT id, nome, descricao, patrimonio_pertence,
             numero_protocolo_plaqueta, local, status, imagem
        FROM itens_cende
        WHERE nome LIKE ?
           OR descricao LIKE ?
           OR patrimonio_pertence LIKE ?
           OR numero_protocolo_plaqueta LIKE ?
           OR local LIKE ?
           OR status LIKE ?
        """,
        (padrao, padrao, padrao, padrao, padrao, padrao),
    )
    itens = cursor.fetchall()
    conexao.close()
    return itens

