from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time


def coletar_dados(navegador):
    dados = []
    linhas = navegador.find_elements(By.XPATH, "//tr")
    for linha in linhas:
        try:
            nome = linha.find_element(
                By.XPATH, './/td[contains(@class, "views-field-field-nome-sgpe")]//a'
            ).text
        except NoSuchElementException:
            nome = None
        try:
            matricula = linha.find_element(
                By.XPATH, './/td[contains(@class, "views-field-field-matricula-sgpe")]'
            ).text
        except NoSuchElementException:
            matricula = None
        try:
            funcao = linha.find_element(
                By.XPATH, './/td[contains(@class, "views-field-field-nome-funcao")]'
            ).text
            if not funcao:
                funcao = "Vazio"
        except NoSuchElementException:
            funcao = "Vazio"
        try:
            email = linha.find_element(
                By.XPATH,
                './/td[contains(@class, "views-field views-field-field-email-sgpe")]',
            ).text
        except NoSuchElementException:
            email = None
        try:
            uf = linha.find_element(
                By.XPATH, './/td[contains(@class, "views-field-field-uf")]'
            ).text
        except NoSuchElementException:
            uf = None
        if nome:
            dados.append(
                {
                    "nome": nome,
                    "matricula": matricula,
                    "funcao": funcao,
                    "email": email,
                    "uf": uf,
                }
            )
    return dados


def preencher_filtros(nav, sigla, itens_por_pagina="40"):
    campo_sigla = nav.find_element(By.ID, "edit-field-siglalotacao-sgpe-value")
    campo_sigla.send_keys(sigla)
    campo_sigla.send_keys(Keys.TAB)
    time.sleep(1)
    select = Select(nav.find_element(By.ID, "edit-items-per-page"))
    select.select_by_visible_text(itens_por_pagina)
    time.sleep(1)
    nav.find_element(By.ID, "views-exposed-form-web-datafone-page").submit()
    time.sleep(10)
