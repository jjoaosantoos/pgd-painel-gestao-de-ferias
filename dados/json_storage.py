import json
import os
from pathlib import Path
from typing import Optional


def _pasta_padrao() -> Path:
    """
    C:\\Users\\<usuario>\\Python\\feriasJson
    """

    home = Path.home()
    pasta = home / "Python" / "feriasJson"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _arquivo_por_sigla(sigla: str) -> Path:
    """
    Retorna:
    ferias_DVGD.json
    ferias_DAED.json
    etc...
    """
    sigla_limpa = (sigla or "").upper().strip()
    nome = f"ferias_{sigla_limpa}.json"
    return _pasta_padrao() / nome


def carregar_dados(sigla: str):
    arquivo = _arquivo_por_sigla(sigla)

    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        if "feriados" not in dados:
            dados["feriados"] = []
            
        return dados
    
    except (FileNotFoundError, json.JSONDecodeError):
        return {"versao": None, 
                "sigla": sigla, 
                "dados": [], 
                "feriados": []
                }


def salvar_dados(dados: dict, sigla: str):
    arquivo = _arquivo_por_sigla(sigla)

    tmp = arquivo.with_suffix(".tmp")

    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    os.replace(tmp, arquivo)


def cadastrar_feriado(sigla: str, dia: int, mes: int, ano: int, tipo: str, uf: str | None):
    dados = carregar_dados(sigla)
    
    novo_feriado = {
        "dia": dia,
        "mes": mes,
        "ano": ano,
        "tipo": tipo,
        "uf": uf,
    }
    
    dados["feriados"].append(novo_feriado)
    salvar_dados(dados, sigla)
    
def remover_feriado(sigla: str, dia: int, mes: int, ano: int, tipo: str, uf: str | None):
    dados = carregar_dados(sigla)

    dados["feriados"] = [
        f for f in dados["feriados"]
        if not (
            f.get("dia") == dia and
            f.get("mes") == mes and
            f.get("ano") == ano and
            f.get("tipo") == tipo and
            f.get("uf") == uf
        )
    ]

    salvar_dados(dados, sigla)

def caminho_padrao_json(sigla: str) -> Path:
    return _arquivo_por_sigla(sigla)
