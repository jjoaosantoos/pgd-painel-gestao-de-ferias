import csv
import calendar
from pathlib import Path
import sys


def pasta_base():
    """
    Retorna a pasta onde está o .exe (produção)
    ou a raiz do projeto (modo desenvolvimento).
    """
    if getattr(sys, 'frozen', False):
        # Quando vira .exe
        return Path(sys.executable).parent
    else:
        # Quando roda pelo Python
        return Path(__file__).resolve().parent.parent


def exportar_calendario_csv(caminho_arquivo, ano, nomes, dados):
    """
    Gera um CSV delimitado por ponto e vírgula,
    compatível com Excel, no formato de grade.

    - Se caminho_arquivo for relativo (ex: "export.csv"), salva dentro do projeto:
      <raiz_do_projeto>/data/exports/export_calendario_<ano>.csv
    - Se caminho_arquivo for absoluto, respeita.
    """

    #Resolver caminho de saída (pra não salvar fora do projeto)
    caminho = Path(caminho_arquivo) if caminho_arquivo else Path()

    # Se veio vazio OU relativo, joga pra dentro do projeto
    if (not caminho_arquivo) or (not caminho.is_absolute()):
        raiz_projeto = pasta_base()
        pasta_exports = raiz_projeto / "exports"
        pasta_exports.mkdir(exist_ok=True)

        caminho = pasta_exports / f"export_calendario_{ano}.csv"


    # 1) Monta todos os dias do ano
    dias_ano = []
    for mes in range(1, 13):
        _, qtd_dias = calendar.monthrange(ano, mes)
        for dia in range(1, qtd_dias + 1):
            dias_ano.append((mes, dia))

    # 2) Cria um mapa rápido: nome -> (mes, dia) -> valor
    mapa = {nome: {} for nome in nomes}

    for item in dados:
        if item.get("ano") != ano:
            continue

        nome = item.get("nome")
        mes = item.get("mes")
        dia = item.get("dia")
        valor = item.get("valor")

        if nome in mapa:
            mapa[nome][(mes, dia)] = valor

    #Escreve o CSV
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")

        # Cabeçalho
        cabecalho = ["Nome"]
        for mes, dia in dias_ano:
            cabecalho.append(f"{dia:02d}/{mes:02d}")
        writer.writerow(cabecalho)

        # Linhas por pessoa
        for nome in nomes:
            linha = [nome]
            for mes, dia in dias_ano:
                linha.append(mapa[nome].get((mes, dia), ""))
            writer.writerow(linha)

    return str(caminho)  # útil pra você mostrar na UI onde salvou
