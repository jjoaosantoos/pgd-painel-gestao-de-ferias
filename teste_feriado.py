from dados.json_storage import cadastrar_feriado, carregar_dados
import json

sigla = "DVGD"

cadastrar_feriado(sigla, 21, 4, 2026, "local", "DF")

dados = carregar_dados(sigla)
print(json.dumps(dados, indent=4, ensure_ascii=False))