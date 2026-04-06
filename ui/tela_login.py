import time
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from automacao.datafone import coletar_dados, preencher_filtros
from ui.tela_principal import TelaPrincipal
from services.datafone_service import buscar_membros_por_area

from pathlib import Path
from dados.json_storage import caminho_padrao_json

def caminho_arquivo_login() -> Path:
    pasta = Path(caminho_padrao_json("TEMP")).parent
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta / "ultimo_login.txt"


def salvar_ultimo_login(email: str, sigla: str):
    arquivo = caminho_arquivo_login()
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(f"email={email.strip()}\n")
        f.write(f"sigla={sigla.strip().upper()}\n")


def carregar_ultimo_login() -> dict:
    arquivo = caminho_arquivo_login()

    if not arquivo.exists():
        return {"email": "", "sigla": ""}

    dados = {"email": "", "sigla": ""}

    with open(arquivo, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()

            if linha.startswith("email="):
                dados["email"] = linha.replace("email=", "", 1)

            elif linha.startswith("sigla="):
                dados["sigla"] = linha.replace("sigla=", "", 1)

    return dados

class TelaLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PGD -> Painel Gestão de Dados")
        self.setGeometry(100, 100, 400, 200)
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout()

        # Email
        linha_email = QHBoxLayout()
        lbl_email = QLabel("Email:")
        lbl_email.setMinimumWidth(50)
        self.entrada_email = QLineEdit()
        self.entrada_email.setMinimumWidth(260)
        self.entrada_email.setStyleSheet("background-color: #e0e0e0;")
        linha_email.addWidget(lbl_email)
        linha_email.addWidget(self.entrada_email)
        linha_email.addStretch()
        layout_principal.addLayout(linha_email)

        # Senha
        linha_senha = QHBoxLayout()
        lbl_senha = QLabel("Senha:")
        lbl_senha.setMinimumWidth(50)
        self.entrada_senha = QLineEdit()
        self.entrada_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.entrada_senha.setMinimumWidth(260)
        self.entrada_senha.setStyleSheet("background-color: #e0e0e0;")
        linha_senha.addWidget(lbl_senha)
        linha_senha.addWidget(self.entrada_senha)
        linha_senha.addStretch()
        layout_principal.addLayout(linha_senha)

        # Sigla + Status
        linha_sigla = QHBoxLayout()
        lbl_sigla = QLabel("Sigla:")
        lbl_sigla.setMinimumWidth(50)
        sigla = self.entrada_sigla = QLineEdit()
        self.entrada_sigla.setFixedWidth(60)
        self.entrada_sigla.setStyleSheet("background-color: #e0e0e0;")
        self.entrada_sigla.textChanged.connect(
            lambda text: self.entrada_sigla.setText(text.upper())
        )
        linha_sigla.addWidget(lbl_sigla)
        linha_sigla.addWidget(self.entrada_sigla)

        self.status_alm = QLabel("ALM")
        self.status_sis = QLabel("SIS")
        self.status_df = QLabel("DATAFONE")
        for lbl in [self.status_alm, self.status_sis, self.status_df]:
            lbl.setFixedSize(60, 20)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                "background-color: lightgray; border: 1px solid black; font-size: 10px; font-weight: bold;"
            )
            linha_sigla.addWidget(lbl)
        linha_sigla.addStretch()
        layout_principal.addLayout(linha_sigla)

        # Botões
        btn_layout = QHBoxLayout()
        btn_entrar = QPushButton("Entrar")
        btn_entrar.clicked.connect(self.fazer_login)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.close)
        btn_layout.addWidget(btn_entrar)
        btn_layout.addWidget(btn_cancelar)
        layout_principal.addLayout(btn_layout)
        
        # Carregar último login
        ultimo_login = carregar_ultimo_login()
        self.entrada_email.setText(ultimo_login["email"])
        self.entrada_sigla.setText(ultimo_login["sigla"])

        self.setLayout(layout_principal)

    def fazer_login(self):
        email = self.entrada_email.text().strip()
        senha = self.entrada_senha.text()
        sigla = self.entrada_sigla.text().strip()

        if not email or not senha:
            QMessageBox.warning(self, "Aviso", "Preencha e-mail e senha.")
            return
        if not sigla:
            QMessageBox.warning(self, "Aviso", "Preencha o campo sigla.")
            return
        if "@" not in email:
            QMessageBox.critical(self, "Erro", "Digite um e-mail válido.")
            return

        usuario = email.split("@")[0]

        opcoes = Options()
        opcoes.add_argument("--ignore-certificate-errors")
        opcoes.add_argument("--ignore-ssl-errors")
        opcoes.add_argument("--log-level=3")
        opcoes.add_argument("--disable-gpu")
        opcoes.add_argument("--no-sandbox")
        opcoes.add_argument("--disable-extensions")
        opcoes.add_argument("--headless")

        try:
            # ALM
            navegador_alm = webdriver.Chrome(options=opcoes)
            url_alm = "https://alm.dataprev.gov.br/ccm"  # URL ALM
            navegador_alm.get(url_alm)
            time.sleep(2)
            navegador_alm.execute_script(
                "document.getElementById('jazz_app_internal_LoginWidget_0_userId').value = arguments[0];",
                usuario,
            )
            navegador_alm.execute_script(
                "document.getElementById('jazz_app_internal_LoginWidget_0_password').value = arguments[0];",
                senha,
            )
            navegador_alm.find_element(By.CLASS_NAME, "j-button-primary").click()
            time.sleep(3)
            navegador_alm.quit()
            self.status_alm.setStyleSheet(
                "background-color: green; border: 1px solid black; font-size: 10px; font-weight: bold; color: white;"
            )
            QApplication.processEvents()

            # SIS
            navegador_sis = webdriver.Chrome(options=opcoes)
            url_sis = "https://www-sisgf/SisGF/faces/pages/acessar.xhtml"  # URL SIS
            navegador_sis.get(url_sis)
            navegador_sis.find_element(By.ID, "j_username").send_keys(usuario)
            navegador_sis.find_element(By.ID, "j_password").send_keys(senha)
            botao = WebDriverWait(navegador_sis, 20).until(
                EC.element_to_be_clickable((By.ID, "btnAcessar"))
            )
            botao.click()
            WebDriverWait(navegador_sis, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(text(),'Sair')]")
                )
            )
            self.status_sis.setStyleSheet(
                "background-color: green; border: 1px solid black; font-size: 10px; font-weight: bold; color: white;"
            )
            QApplication.processEvents()
            
            # Datafone -> via service
            dados = buscar_membros_por_area(sigla, url_datafone="https://www-conexao/servicos/webdatafone")

            
            self.status_df.setStyleSheet(
                "background-color: green; border: 1px solid black; font-size: 10px; font-weight: bold; color: white;"
            )
            QApplication.processEvents()
            #  SALVA ANTES DE ABRIR A TELA
            salvar_ultimo_login(email, sigla)

            self.hide()
            self.tela_principal = TelaPrincipal(dados, sigla)
            self.tela_principal.showMaximized()

        except Exception as e:
            QMessageBox.critical(self, "Erro Técnico", f"Erro: {e}")
