import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QPushButton,
    QHBoxLayout,
    QLabel,
)
from PyQt6.QtCore import Qt, QTimer

from ui.calendario_ano import CalendarioAno
from dados.json_storage import carregar_dados, salvar_dados, caminho_padrao_json

from dados.db_repository import salvar_nova_versao, buscar_dados_atuais
from utils.export_csv import exportar_calendario_csv


from pathlib import Path

from PyQt6.QtWidgets import QFileDialog
from config import get_output_dir, set_output_dir, build_paths



class TelaPrincipal(QWidget):
    def __init__(self, dados, sigla):
        super().__init__()

        self.sigla = sigla

        resultado = buscar_dados_atuais(self.sigla)

        if resultado:
            self.versao_atual = resultado["versao"]
        else:
            self.versao_atual = "N/A"

        self.atualizar_titulo_janela()

        self.setGeometry(100, 100, 1600, 700)

        self.dados = dados
        
        # JSON SEMPRE no caminho padrão por usuário
        caminho_json = Path(caminho_padrao_json(self.sigla))
        caminho_json_inicial = str(caminho_json)

        if caminho_json.exists():
            # já existe JSON local: carrega e preenche (comportamento atual)
            json_local = carregar_dados(self.sigla)
        else:
            # primeira vez: consulta banco automaticamente
            resultado_auto = buscar_dados_atuais(self.sigla)

            if resultado_auto:
                versao = resultado_auto["versao"]
                dados_bd = self._filtrar_dados_sigla(resultado_auto.get("dados", []))

                json_local = {"versao": versao, "sigla": self.sigla, "dados": dados_bd}

                # cria o arquivo local automaticamente
                salvar_dados(json_local, self.sigla)

                # já atualiza as versões em memória pra UI/botão
                self.versao_atual = versao
                self.atualizar_titulo_janela()
            else:
                # não tem nada no banco: segue vazio
                json_local = {"versao": None, "sigla": self.sigla, "dados": []}


        # Compatibilidade com JSON antigo (lista)
        if isinstance(json_local, list):
            self.versao_json = None
            self.dados_salvos = self._filtrar_dados_sigla(json_local)
        else:
            self.versao_json = json_local.get("versao")
            self.dados_salvos = self._filtrar_dados_sigla(json_local.get("dados", []))

        self.dados_consultados = None

        # Identifica anos existentes
        anos_existentes = sorted(
            set(
                item.get("ano", datetime.datetime.now().year)
                for item in self.dados_salvos
            )
        )

        ano_atual = datetime.datetime.now().year
        mes_atual = datetime.datetime.now().month

        if ano_atual not in anos_existentes:
            anos_existentes.append(ano_atual)

        if mes_atual >= 6:
            proximo_ano = ano_atual + 1
            if proximo_ano not in anos_existentes:
                anos_existentes.append(proximo_ano)

        self.calendarios = {}
        self.ano_atual = ano_atual

        for ano in sorted(anos_existentes):
            calendario = CalendarioAno(
                self.dados,
                self.dados_salvos,
                self.sigla,
                ano,
                caminho_json=caminho_json_inicial,
            )
            self.calendarios[ano] = calendario
            calendario.setVisible(ano == ano_atual)
            calendario.dados_alterados.connect(self.atualizar_dados)

        btn_salvar = QPushButton("Salvar")
        self.btn_consultar = QPushButton("Consultar")
        btn_exportar = QPushButton("Exportar CSV")

        btn_salvar.clicked.connect(self.on_salvar_click)
        self.btn_consultar.clicked.connect(self.on_consultar_click)
        btn_exportar.clicked.connect(self.on_exportar_click)

        layout_geral = QVBoxLayout(self)

        # ===== TOPO DA TELA =====

        # 1. Layout dos botões (lado esquerdo)
        layout_botoes = QHBoxLayout()
        layout_botoes.addWidget(btn_salvar)
        layout_botoes.addWidget(self.btn_consultar)
        layout_botoes.addWidget(btn_exportar)

        # 3. Layout principal do topo
        layout_topo = QHBoxLayout()
        layout_topo.addLayout(layout_botoes)
        layout_topo.addStretch()
        layout_topo.addStretch()

        # 4. Adiciona o topo ao layout geral
        layout_geral.addLayout(layout_topo)

        for calendario in self.calendarios.values():
            layout_geral.addWidget(calendario)
        self.setLayout(layout_geral)

        # Define cor inicial do botão Consultar
        resultado = buscar_dados_atuais(self.sigla)
        versao_banco = resultado["versao"] if resultado else None

        # Se não existe nada no banco pra essa sigla, não pode estar "desatualizado"
        if versao_banco is None:
            self.atualizar_status_consultar(False)
            self.btn_consultar.setToolTip(
                "Não existem dados salvos no banco para esta área"
            )
        else:
            desatualizado = self.versao_json != versao_banco
            self.atualizar_status_consultar(desatualizado)

        self.timer_verificacao = QTimer(self)
        self.timer_verificacao.timeout.connect(self.verificar_versao_banco)
        self.timer_verificacao.start(45000)  # 5 segundos

    def atualizar_dados(self, novos_dados):
        self.dados_salvos = novos_dados

    def _filtrar_dados_sigla(self, dados: list[dict]) -> list[dict]:
        s = (self.sigla or "").upper().strip()
        filtrado = []
        for item in dados or []:
            sig = (item.get("sigla") or "").upper().strip()
            if sig == s:
                filtrado.append(item)
        return filtrado

    def _garantir_paths_saida(self) -> dict | None:
        """
        Se for a primeira vez, pergunta a pasta e memoriza.
        Retorna dict com paths (base_dir, pasta_exports, pasta_projeto, arquivo_json).
        """
        base_dir = get_output_dir()

        if base_dir is None:
            pasta = QFileDialog.getExistingDirectory(
                self,
                "Escolha a pasta para salvar e exportar",
                str(Path.home()),
            )
            if not pasta:
                return None  # usuário cancelou
            base_dir = set_output_dir(pasta)

        paths = build_paths(base_dir, self.sigla)

        # Atualiza o label do caminho em TODOS os calendários (pra refletir o local real)
        for cal in self.calendarios.values():
            cal.set_caminho_json(str(caminho_padrao_json(self.sigla)))

        return paths

    def on_salvar_click(self):
        if not self.dados_salvos:
            QMessageBox.warning(self, "Aviso", "Não há dados para salvar.")
            return

        try:
            # 0) Dados que o usuário quer salvar (da tela)
            dados_para_salvar = self._filtrar_dados_sigla(self.dados_salvos)

            # 1) Pega o que já está no banco hoje
            atual = buscar_dados_atuais(self.sigla)
            dados_banco = self._filtrar_dados_sigla(atual["dados"]) if atual else []
            versao_banco = atual["versao"] if atual else None

            # 2) Se for igual, não cria versão nova
            if self._normalizar_registros(dados_para_salvar) == self._normalizar_registros(dados_banco):
                QMessageBox.information(
                    self,
                    "Nada para salvar",
                    f"Nenhuma alteração foi detectada.\n"
                    f"A área {self.sigla} já está sincronizada com o banco."
                    + (f"\nVersão atual: {versao_banco}" if versao_banco is not None else "")
                )
                self.atualizar_status_consultar(False)
                return

            # 3) Se mudou, salva no banco (gera NOVA versão)
            salvar_nova_versao(area=self.sigla, dados=dados_para_salvar)

            # 4) Busca a versão oficial recém-criada
            resultado = buscar_dados_atuais(self.sigla)
            versao = resultado["versao"]

            self.versao_atual = versao
            self.versao_json = versao
            self.atualizar_titulo_janela()

            # 5) Atualiza JSON local por sigla
            json_versionado = {
                "versao": versao,
                "sigla": self.sigla,
                "dados": dados_para_salvar,
            }
            salvar_dados(json_versionado, self.sigla)

            self.dados_salvos = dados_para_salvar
            self.atualizar_status_consultar(False)

            QMessageBox.information(
                self,
                "Sucesso",
                f"Dados salvos com sucesso!\nÁrea: {self.sigla}\nVersão: {versao}",
            )

        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", str(e))


    def _normalizar_registros(self, registros: list[dict]) -> list[dict]:
        """
        Normaliza para comparar "conteúdo", ignorando diferenças bobas (ordem, espaços).
        Ajuste as chaves conforme seu dict real.
        """
        def norm_str(v):
            return v.strip() if isinstance(v, str) else v

        normalizado = []
        for r in (registros or []):
            item = {
                "sigla": (norm_str(r.get("sigla")) or "").upper(),
                "nome": (norm_str(r.get("nome")) or "").upper(),
                "ano": int(r.get("ano")) if r.get("ano") is not None else None,
                "mes": int(r.get("mes")) if r.get("mes") is not None else None,
                "dia": int(r.get("dia")) if r.get("dia") is not None else None,
                "tipo": (norm_str(r.get("tipo")) or "").upper(),
            }
            normalizado.append(item)

        normalizado.sort(key=lambda x: (
            x["sigla"], x["nome"],
            x["ano"] or 0, x["mes"] or 0, x["dia"] or 0,
            x["tipo"]
        ))
        return normalizado


    def on_consultar_click(self):
        try:
            # Busca a última versão no banco
            resultado = buscar_dados_atuais(self.sigla)

            if not resultado:
                self.atualizar_status_consultar(False)

                QMessageBox.information(
                    self,
                    "Consulta",
                    "Não existem dados salvos no banco para esta área.",
                )
                return

            versao = resultado["versao"]

            self.versao_atual = versao
            self.atualizar_status_consultar(False)

            dados_bd = resultado["dados"]
            dados_bd = self._filtrar_dados_sigla(dados_bd)

            # Atualiza versão em memória
            self.versao_json = versao

            # Atualiza JSON local para refletir o banco
            json_versionado = {"versao": versao, "sigla": self.sigla, "dados": dados_bd}
            salvar_dados(json_versionado, self.sigla)  # padrão, não pergunta pasta

            # Atualiza título da janela
            self.atualizar_titulo_janela()

            # Filtra apenas o ano atualmente visível
            dados_ano_atual = [
                item for item in dados_bd if item.get("ano") == self.ano_atual
            ]

            # Guarda exatamente o que o CSV precisa
            self.dados_consultados = {"versao": versao, "registros": dados_ano_atual}

            # Atualiza estado interno completo
            self.dados_salvos = dados_bd

            # Atualiza SOMENTE o calendário do ano atual (mas com dados completos)
            calendario = self.calendarios.get(self.ano_atual)
            if calendario:
                calendario.atualizar_dados(dados_bd)
                calendario.limpar_filtro()

            QMessageBox.information(
                self,
                "Consulta",
                f"Dados do ano {self.ano_atual} atualizados com sucesso!\nVersão no Banco de Dados: {versao}",
            )

        except Exception as e:
            QMessageBox.critical(self, "Erro na consulta", str(e))

    def _exportar_csv_do_ano_atual(self):
        ano = self.ano_atual
        sigla = self.sigla

        calendario = self.calendarios.get(ano)
        if not calendario:
            QMessageBox.warning(
                self, "Exportar", "Calendário do ano atual não encontrado."
            )
            return

        nomes_interface = calendario.obter_nomes()
        dados_json = self.dados_salvos or []
        nome_arquivo = f"calendario_{sigla}_{ano}.csv"

        caminho_arquivo, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar CSV",
            str(Path.home() / nome_arquivo),
            "Arquivos CSV (*.csv)"
        )

        if not caminho_arquivo:
            return  # usuário cancelou

        caminho_final = exportar_calendario_csv(
            caminho_arquivo=caminho_arquivo,
            ano=ano,
            nomes=nomes_interface,
            dados=dados_json,
        )

        QMessageBox.information(
            self,
            "Exportação",
            f"Arquivo gerado com sucesso!\n\n{caminho_final}"
        )

    def on_exportar_click(self):
        try:
            # 1) Verifica se existe versão mais nova no banco
            resultado = buscar_dados_atuais(self.sigla)
            versao_banco = resultado["versao"] if resultado else None

            desatualizado = (self.versao_json != versao_banco) and (
                versao_banco is not None
            )

            if desatualizado:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Exportar CSV")
                msg.setText(
                    "Existe uma versão mais recente no banco.\nDeseja consultar antes de exportar?"
                )
                msg.setInformativeText(
                    f"Sua versão local: {self.versao_json}\n"
                    f"Versão no banco: {versao_banco}"
                )

                btn_consultar_exportar = msg.addButton(
                    "Consultar e exportar", QMessageBox.ButtonRole.AcceptRole
                )
                btn_exportar_mesmo = msg.addButton(
                    "Exportar mesmo assim", QMessageBox.ButtonRole.DestructiveRole
                )
                msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)

                msg.exec()
                botao_clicado = msg.clickedButton()

                if botao_clicado == btn_consultar_exportar:
                    # chama a consulta (vai atualizar self.dados_salvos e self.versao_json)
                    self.on_consultar_click()
                    # depois exporta
                    self._exportar_csv_do_ano_atual()
                    return

                if botao_clicado == btn_exportar_mesmo:
                    self._exportar_csv_do_ano_atual()
                    return

                # Cancelar
                return

            # 2) Se não estiver desatualizado, exporta direto
            self._exportar_csv_do_ano_atual()

        except PermissionError:
            QMessageBox.critical(
                self,
                "Erro na exportação",
                "Permissão negada ao salvar o arquivo.\n\n"
                "Feche o CSV no Excel (ou qualquer programa que esteja usando o arquivo) e tente novamente.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro na exportação", str(e))

    def verificar_versao_banco(self):
        resultado = buscar_dados_atuais(self.sigla)

        # Se não existe nada no banco pra essa área, deixa verde/neutro + tooltip certo
        if not resultado:
            self.atualizar_status_consultar(False)
            self.btn_consultar.setToolTip(
                "Não existem dados salvos no banco para esta área"
            )
            return

        versao_banco = resultado["versao"]

        if self.versao_json != versao_banco:
            self.atualizar_status_consultar(True)  # Vermelho
        else:
            self.atualizar_status_consultar(False)  # Verde

    def atualizar_status_consultar(self, desatualizada: bool):
        if desatualizada:
            self.btn_consultar.setStyleSheet(
                """
                background-color: #d32f2f;
                color: white;
                font-weight: bold;
            """
            )
            self.btn_consultar.setToolTip("Existe uma versão mais recente no banco")
        else:
            self.btn_consultar.setStyleSheet(
                """
                background-color: #2e7d32;
                color: white;
                font-weight: bold;
            """
            )
            self.btn_consultar.setToolTip("Você está usando a versão mais recente")

    def atualizar_titulo_janela(self):
        self.setWindowTitle(
            f"PGD - Painel Gestão de Dados ({self.sigla}) - Versão Banco de Dados: {self.versao_atual}"
        )
