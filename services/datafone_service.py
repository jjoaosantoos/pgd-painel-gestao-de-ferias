
import os
import time
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from automacao.datafone import preencher_filtros, coletar_dados


def _criar_opcoes_chrome(headless: bool = True) -> Options:
    """
    Centraliza as opções do Chrome.
    - Motivo: UI e API vão usar o mesmo padrão, sem duplicar código.
    """
    opcoes = Options()
    opcoes.add_argument("--ignore-certificate-errors")
    opcoes.add_argument("--ignore-ssl-errors")
    opcoes.add_argument("--log-level=3")
    opcoes.add_argument("--disable-gpu")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-extensions")
    if headless:
        opcoes.add_argument("--headless")
    return opcoes


def buscar_membros_por_area(
    area: str,
    *,
    url_datafone: Optional[str] = None,
    itens_por_pagina: str = "40",
    headless: bool = True,
) -> List[Dict[str, str]]:

    area = (area or "").strip().upper()
    if not area:
        raise ValueError("Área (sigla) não pode ser vazia.")

    url = url_datafone or "https://www-conexao/servicos/webdatafone"
    if not url:
        raise ValueError(
            "URL do Datafone não informada. Passe url_datafone=... ou defina DATAFONE_URL no ambiente."
        )

    opcoes = _criar_opcoes_chrome(headless=headless)

    driver = None
    try:
        driver = webdriver.Chrome(options=opcoes)
        driver.get(url)

        time.sleep(1)

        preencher_filtros(driver, area, itens_por_pagina=itens_por_pagina)
        dados = coletar_dados(driver)
        return dados

    finally:
        # garante que o navegador fecha mesmo se der erro
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
