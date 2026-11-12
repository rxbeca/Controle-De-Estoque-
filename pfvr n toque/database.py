#EXTENSÕES DE BIBLBIOTECAS 


import sqlite3
import hashlib
import os
import binascii

#ONDE SE CRIA O BANCO DE DADOS E AS TABELAS PRA O QUE CADA UM VAI RECEBER

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
            imagem TEXT,
            categoria TEXT NOT NULL DEFAULT ''
        )
        """
    )

    colunas_itens = {
        coluna[1] for coluna in cursor.execute("PRAGMA table_info(itens_cende)").fetchall()
    }
    #ONDE AS IMAGENS SERAM ADCIONADAS 

    if "imagem" not in colunas_itens:
        cursor.execute("ALTER TABLE itens_cende ADD COLUMN imagem TEXT")
    if "categoria" not in colunas_itens:
        cursor.execute("ALTER TABLE itens_cende ADD COLUMN categoria TEXT NOT NULL DEFAULT ''")

#A DOS ARMARIOS 
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS armarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            imagem TEXT,
            patrimonio TEXT DEFAULT ''
        )
        """
    )

    colunas_armarios = {
        coluna[1] for coluna in cursor.execute("PRAGMA table_info(armarios)").fetchall()
    }
    #MESMA COISA DAS IMAGENS DA OUTR TABELA
     
    if "imagem" not in colunas_armarios:
        cursor.execute("ALTER TABLE armarios ADD COLUMN imagem TEXT")
    if "protocolo" not in colunas_armarios:
        cursor.execute("ALTER TABLE armarios ADD COLUMN protocolo TEXT DEFAULT ''")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS itens_armario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            armario_id INTEGER NOT NULL,
            nome_item TEXT NOT NULL,
            imagem TEXT,
            patrimonio TEXT DEFAULT '',
            categoria TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (armario_id) REFERENCES armarios(id)
        )
        """
    )

    colunas_itens_armario = {
        coluna[1] for coluna in cursor.execute("PRAGMA table_info(itens_armario)").fetchall()
    }
    if "patrimonio" not in colunas_itens_armario:
        cursor.execute("ALTER TABLE itens_armario ADD COLUMN patrimonio TEXT DEFAULT ''")
        if "patrimonio_item" in colunas_itens_armario:
            cursor.execute(
                """
                UPDATE itens_armario
                SET patrimonio = patrimonio_item
                WHERE patrimonio_item IS NOT NULL AND TRIM(patrimonio_item) <> ''
                """
            )
    if "imagem" not in colunas_itens_armario:
        cursor.execute("ALTER TABLE itens_armario ADD COLUMN imagem TEXT")
    if "protocolo" not in colunas_itens_armario:
        cursor.execute("ALTER TABLE itens_armario ADD COLUMN protocolo TEXT DEFAULT ''")
    if "categoria" not in colunas_itens_armario:
        cursor.execute("ALTER TABLE itens_armario ADD COLUMN categoria TEXT NOT NULL DEFAULT ''")

# USUARIO(LOGIN)
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
#OS ARMARIOS ONDE CADA ITEM OIDE SER COLOCADO
    cursor.execute("SELECT COUNT(*) FROM armarios")
    if cursor.fetchone()[0] == 0:
        armarios_iniciais = [
            ("Armário 1", ""),
            ("Armário 2", ""),
            ("Armário 3", ""),
            ("Armário A", ""),
            ("Armário B", ""),
            ("Armário C", ""),
        ]
        cursor.executemany("INSERT INTO armarios (nome, protocolo) VALUES (?, ?)", armarios_iniciais)

    conexao.commit()
    conexao.close()

# SENHA 
def _hash_password(password: str, salt: bytes = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    return binascii.hexlify(salt).decode() + ':' + binascii.hexlify(dk).decode()

#VERIFICAÇÃO DE SENHA 

def _verify_password(stored_hash: str, password: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split(':')
        salt = binascii.unhexlify(salt_hex)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
        return binascii.hexlify(dk).decode() == hash_hex
    except Exception:
        return False

# VERIFICA A VERACIDADE DA CONTA CADASTRADA 
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

# CRIAR UM NOVO USUARIO 
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

#ONDE COMECA A LISTA  DA TABELA DE ITENS DO CENDE
def listar_itens_cende():
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT id, nome, descricao, patrimonio_pertence, numero_protocolo_plaqueta, local, status, imagem, categoria FROM itens_cende"
    )
    itens = cursor.fetchall()
    conexao.close()
    return itens

#ADICIONAR ITENS NA TABELA DO CENDE 
def inserir_item_cende(nome, descricao, patrimonio, plaqueta, local, status, imagem=None, categoria=""):
    categoria = (categoria or "").strip()
    if not categoria:
        return False, "Categoria é obrigatória."

    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO itens_cende (nome, descricao, patrimonio_pertence, numero_protocolo_plaqueta, local, status, imagem, categoria)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (nome, descricao, patrimonio, plaqueta, local, status, imagem, categoria),
        )
        conexao.commit()
        return True, "Item cadastrado com sucesso!"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()

#FAZ COM Q SEJA POSSIVEL ATUALIZAR UM ITEM POR COLUNA ESPECIFICA, COMO NOME, DESCRIÇÃO, PATRIMONIO, PLAQUETA, LOCAL, STATUS, IMAGEM OU CATEGORIA
def atualizar_item_por_coluna(item_id: int, coluna: str, valor):
    colunas_permitidas = {
        "nome": "nome",
        "descricao": "descricao",
        "patrimonio": "patrimonio_pertence",
        "plaqueta": "numero_protocolo_plaqueta",
        "local": "local",
        "status": "status",
        "imagem": "imagem",
        "categoria": "categoria",
    }

    if coluna not in colunas_permitidas:
        return False, "Coluna inválida."
    if coluna == "categoria":
        valor = str(valor or "").strip()
        if not valor:
            return False, "Categoria é obrigatória."

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

#EDITA OS ITENS PRESENTES NA TABELA 
def edicao_de_itens(item_id, nome, descricao, patrimonio, plaqueta, local, status, imagem, protocolo=None, itens_armarios=None, categoria=""):
    categoria = (categoria or "").strip()
    if not categoria:
        return False, "Categoria é obrigatória."

    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute(
            """
            UPDATE itens_cende
            SET nome = ?, descricao = ?, patrimonio_pertence = ?, numero_protocolo_plaqueta = ?, local = ?, status = ?, imagem = COALESCE(?, imagem), categoria = ?
            WHERE id = ?
            """,
            (nome, descricao, patrimonio, plaqueta, local, status, imagem, categoria, item_id),
        )

        if itens_armarios is not None:
            cursor.execute(
                """
                UPDATE itens_armario
                SET nome_item = ?, patrimonio = ?, imagem = COALESCE(?, imagem)
                WHERE id = ?
                """,
                (nome, patrimonio, imagem, itens_armarios),
            )

        conexao.commit()
        return True, "Item atualizado com sucesso!"
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()

#EXCLUIR ITENS
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

# AQ PARTE DA MESMA LOGICA DOS DEFS PARA OS ITENS DO CENDE, EH A MESMA LOGICA PARA OS ARMARIOS 
def listar_armarios_com_itens():
    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT a.id, a.nome, ia.id, ia.nome_item, ia.imagem, ia.patrimonio, ia.categoria
        FROM armarios AS a
        LEFT JOIN itens_armario AS ia ON ia.armario_id = a.id
        ORDER BY a.id, ia.id
        """
    )

    armarios = {}
    for armario_id, nome, item_id, nome_item, imagem, patrimonio, categoria in cursor.fetchall():
        if armario_id not in armarios:
            armarios[armario_id] = {"id": armario_id, "nome": nome, "itens": []}
        if item_id is not None:
            armarios[armario_id]["itens"].append(
                {"id": item_id, "nome": nome_item, "imagem": imagem, "patrimonio": patrimonio, "categoria": categoria}
            )

    conexao.close()
    return list(armarios.values())

# ANTES DE ADICIONAR UM ITEM AO ARMARIO, ELE VERIFICA SE O NOME, PATRIMONIO E CATEGORIA ESTÃO PRESENTES, SE NAO ESTIVEREM, ELE RETORNA UMA MENSAGEM DE ERRO
def inserir_item_armario(armario_id: int, nome_item: str, imagem=None, patrimonio: str = "", categoria: str = ""):
    nome_item = (nome_item or "").strip()
    patrimonio = (patrimonio or "").strip()
    categoria = (categoria or "").strip()
    if not nome_item:
        return False, "Nome do item é obrigatório."
    if not patrimonio:
        return False, "Patrimonio  é obrigatório."
    if not categoria:
        return False, "Categoria é obrigatória."

    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT id FROM armarios WHERE id = ?", (armario_id,))
        if cursor.fetchone() is None:
            return False, "Armário não encontrado."

        cursor.execute(
            "INSERT INTO itens_armario (armario_id, nome_item, imagem, patrimonio, categoria) VALUES (?, ?, ?, ?, ?)",
            (armario_id, nome_item, imagem, patrimonio, categoria),
        )
        conexao.commit()
        return True, "Item adicionado ao armário."
    except Exception as e:
        conexao.rollback()
        return False, str(e)
    finally:
        conexao.close()


def atualizar_item_armario(item_id: int, nome_item: str, patrimonio: str, imagem=None, categoria: str = ""):
    categoria = (categoria or "").strip()
    if not nome_item or not nome_item.strip():
        return False, "Nome do item é obrigatório."
    if not patrimonio or not patrimonio.strip():
        return False, "Patrimonio  é obrigatório."
    if not categoria:
        return False, "Categoria é obrigatória."

    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    try:
        cursor.execute(
            "UPDATE itens_armario SET nome_item = ?, patrimonio = ?, imagem = COALESCE(?, imagem), categoria = ? WHERE id = ?",
            (nome_item.strip(), patrimonio.strip(), imagem, categoria, item_id),
        )
        conexao.commit()
        return True, "Item atualizado com sucesso."
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
# ONDE SE PESQUISA ITENS DA TABELA PRINCIPAL E DOS ARMARIOS 
def pesquisar_item(termo):
    termo = (termo or '').strip()
    if not termo:
        return listar_itens_cende()

    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    padrao = f"%{termo}%"
    try:
        cursor.execute(
            """
            SELECT id, nome, descricao, patrimonio_pertence,
                   numero_protocolo_plaqueta, local, status, imagem, categoria
            FROM itens_cende
            WHERE TRIM(COALESCE(nome, '')) LIKE ?
               OR TRIM(COALESCE(descricao, '')) LIKE ?
               OR TRIM(COALESCE(patrimonio_pertence, '')) LIKE ?
               OR TRIM(COALESCE(numero_protocolo_plaqueta, '')) LIKE ?
               OR TRIM(COALESCE(local, '')) LIKE ?
               OR TRIM(COALESCE(status, '')) LIKE ?
            ORDER BY nome COLLATE NOCASE
            """,
            (padrao, padrao, padrao, padrao, padrao, padrao),
        )
        return cursor.fetchall()
    finally:
        conexao.close()

# ADIÇAO DE ATRIBUTOS PARA PESQUISA DE ITENS, COMO NOME, LOCAL E STATUS, PARA FACILITAR A BUSCA DE ITENS ESPECIFICOS
def listar_valores_atributo(atributo):
    colunas_permitidas = {"nome": "Nome", "local": "Local", "status": "Status"}
    coluna = colunas_permitidas.get(atributo)
    if coluna is None:
        return []

    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    cursor.execute(
        f"SELECT DISTINCT TRIM({coluna}) FROM itens_cende "
        f"WHERE TRIM({coluna}) <> '' ORDER BY TRIM({coluna}) COLLATE NOCASE"
    )
    valores = [linha[0] for linha in cursor.fetchall()]
    conexao.close()
    return valores

# ESSE EH PARA OS ARAMRIOS 
def listar_itens_por_atributo(atributo, valor):
    colunas_permitidas = {"nome": "Nome", "local": "Local", "status": "Status"}
    coluna = colunas_permitidas.get(atributo)
    if coluna is None:
        return []

    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    cursor.execute(
        f"""
        SELECT id, nome, descricao, patrimonio_pertence,
               numero_protocolo_plaqueta, local, status, imagem
        FROM itens_cende
        WHERE TRIM({coluna}) = TRIM(?) COLLATE NOCASE
        ORDER BY nome COLLATE NOCASE
        """,
        (valor,),
    )
    itens = cursor.fetchall()
    conexao.close()
    return itens

# A PARTE DE PESQUISA DE IRENS PARA A CRIAÇÃO DOS REALTORIOS 
def pesquisar_itens_relatorio(termo):
    termo = (termo or "").strip()
    if not termo:
        return []

    conexao = sqlite3.connect("estoque.db")
    cursor = conexao.cursor()
    padrao = f"%{termo}%"
    cursor.execute(
        """
         SELECT nome, descricao, categoria, patrimonio_pertence,
             numero_protocolo_plaqueta, local, status, 'Estoque geral' AS origem
        FROM itens_cende
         WHERE nome LIKE ? COLLATE NOCASE OR descricao LIKE ? COLLATE NOCASE OR categoria LIKE ? COLLATE NOCASE

        UNION ALL

         SELECT ia.nome_item, '', ia.categoria, '', ia.patrimonio,
             a.nome, 'ARMÁRIO', 'Armário: ' || a.nome AS origem
        FROM itens_armario AS ia
        JOIN armarios AS a ON a.id = ia.armario_id
          WHERE ia.nome_item LIKE ? COLLATE NOCASE OR ia.patrimonio LIKE ? COLLATE NOCASE
              OR ia.categoria LIKE ? COLLATE NOCASE OR a.nome LIKE ? COLLATE NOCASE
          ORDER BY nome COLLATE NOCASE
        """,
          (padrao, padrao, padrao, padrao, padrao, padrao, padrao),
    )
    itens = cursor.fetchall()
    conexao.close()
    return itens
