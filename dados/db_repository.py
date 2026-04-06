import json
import psycopg2  # biblioteca que conversa com PostgreSQL

print(">>> db_repository.py CORRETO FOI CARREGADO <<<")


def get_conexao():
    conn = psycopg2.connect(
        user="cdados",
        password="dataprev00",
        host="n111d003790.fast.prevnet",
        port=5433,
        database="pgsx_dev_catalogodadosweb",
    )

    with conn.cursor() as cur:
        cur.execute("SELECT current_database();")
        print(">>> BANCO CONECTADO:", cur.fetchone())

        cur.execute("SHOW search_path;")
        print(">>> SEARCH_PATH:", cur.fetchone())

    return conn


def obter_versao_atual(area):
    """
    Retorna a maior versão salva para a área informada.
    Se não existir nenhuma, retorna 0.
    """
    sql = """
        SELECT COALESCE(MAX(nu_versao), 0)
        FROM cdados.painel_gestao_dados_ausencias
        WHERE nm_area = %s
    """

    with get_conexao() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (area,))
            return cur.fetchone()[0]


def salvar_nova_versao(area, dados):
    """
    Salva uma nova versão no banco (versão atual + 1).
    """
    versao_atual = obter_versao_atual(area)
    nova_versao = versao_atual + 1

    sql = """
        INSERT INTO cdados.painel_gestao_dados_ausencias
        (nu_versao, nm_area, te_json)
        VALUES (%s, %s, %s)
    """

    with get_conexao() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (nova_versao, area, json.dumps(dados, ensure_ascii=False)))


def buscar_dados_atuais(area):
    sql = """
        SELECT nu_versao, te_json
        FROM cdados.painel_gestao_dados_ausencias
        WHERE nm_area = %s
        ORDER BY nu_versao DESC
        LIMIT 1
    """

    with get_conexao() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (area,))
            resultado = cur.fetchone()

            if not resultado:
                return None

            versao, te_json = resultado

            return {"versao": versao, "dados": te_json}
