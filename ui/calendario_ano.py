import calendar
from datetime import datetime


from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QAbstractItemView

from pathlib import Path


class CalendarioAno(QWidget):
    """Cria uma aba com o calendário de um determinado ano (opção A: grade única)"""

    def __init__(
        self,
        dados,
        dados_salvos,
        sigla,
        ano=None,
        caminho_json: str | Path | None = None,
    ):

        super().__init__()

        self.carregando = True
        self.sigla = sigla
        self.dados = dados
        self.dados_salvos = dados_salvos
        self.row_por_nome = {}
        self.caminho_json = str(caminho_json) if caminho_json else ""

        # Detecta o Ano Atual
        from datetime import datetime

        hoje = datetime.now()
        self.ano = int(hoje.year if ano is None else ano)

        # Dicionario de meses
        self.meses_pt = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro",
        }

        self.celulas = []
        self.labels_nomes = []
        self.linhas_por_nome = {}

        self.cores_manual = {
            "F": "green",
            "L": "orange",
            "A": "lightBlue",
            "T": "thistle",
            "R": "red",
            "O": "yellow",
            "P": "gray",
            "S": "brown",
            "E": "magenta",
        }
        
        self.codigos_bloqueados = {"F", "L"}

        # --- Manual de caracteres ---
        manual_frame = (
            QFrame()
        )  # Cria um quadro (barrinha no topo) onde ficam as legendas
        manual_layout = QHBoxLayout(manual_frame)  # Layout horizontal
        manual_frame.setFixedHeight(43)  # Altura de 43 pixels

        def criar_label(texto, cor, tooltip=None):
            label = QLabel(texto)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                f"font-size: 13px; font-weight: bold; color: white; "
                f"background-color: {cor}; border-radius: 6px; padding: 6px;"
            )

            if tooltip:
                label.setToolTip(tooltip)

            return label

        # Para cada pas Texto/Cor -> Cria uma etiqueta
        for texto, cor, self.toolTip in [
            ("* F - Férias", "green", "Importado automaticamente de outra plataforma. Não pode ser registrado manualmente"),
            ("* L - Licença Prêmio", "orange", "Importado automaticamente de outra plataforma. Não pode ser registrado manualmente"),
            ("A - Abono", "lightBlue", None),
            ("T - Folga TRE", "thistle", None),
            ("R - Recesso", "red", None),
            ("O - Outras Ausências", "#FFE066", None),
            ("P - Ausências Parciais", "gray", None),
            ("S - Substituição", "brown", None),
            ("E - Eventos/Treinamento", "magenta", None),
        ]:
            manual_layout.addWidget(criar_label(texto, cor, self.toolTip))  # Adiciona no Layout

        self.label_lider = QLabel("Líder:")
        self.label_lider.setStyleSheet("font-size: 13px; font-weight: bold;")
        
        self.combo_opcoes = QComboBox()
        self.combo_opcoes.setFixedWidth(250)
        self.combo_opcoes.setPlaceholderText("Líder de Equipe")

        for lider in self.obter_lideres_equipe():
            self.combo_opcoes.addItem(lider)

        # Criando campo de pesquisa
        pesquisa_layout = QHBoxLayout()
        pesquisa_label = QLabel("Pesquisar:")  
        self.campo_pesquisa = QLineEdit()
        self.campo_pesquisa.setPlaceholderText("Digite um nome...")
        self.campo_pesquisa.textChanged.connect(self.filtrar_nomes)
        pesquisa_layout.addWidget(pesquisa_label)
        pesquisa_layout.addWidget(self.campo_pesquisa)

        # Criando Tabela Nomes
        self.table_nomes = QTableWidget()
        self.table_nomes.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )

        self.table_nomes.setColumnCount(1)
        self.table_nomes.setHorizontalHeaderLabels(["Nome"])  # Cabecalho
        self.table_nomes.verticalHeader().setVisible(False)
        self.table_nomes.horizontalHeader().setStretchLastSection(True)
        self.table_nomes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # garante mesma altura de linha da grade
        ALTURA_LINHA = 30
        self.table_nomes.verticalHeader().setDefaultSectionSize(ALTURA_LINHA)

        # --- Ajustes na tabela de nomes para scroll horizontal ---
        self.table_nomes.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table_nomes.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)

        # Permitir que a tabela mostre scroll horizontal quando necessário
        self.table_nomes.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.table_nomes.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Largura Minima
        self.table_nomes.setMinimumWidth(300)

        self.table_nomes.setMinimumWidth(300)

        self.table_nomes.horizontalHeader().setVisible(False)

        self.table_nomes.setFrameShape(QFrame.Shape.NoFrame)

        # --- Linhas fantasma para alinhar perfeitamente com cabeçalho (3 linhas) ---
        self.table_nomes.setRowCount(len(self.dados))

        # Layout nomes
        self.nomes_layout = QVBoxLayout()
        self.nomes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.nomes_layout.addWidget(self.table_nomes)

        self.nomes_container = QWidget()
        self.nomes_container.setFixedWidth(320)

        self.nomes_container.setLayout(self.nomes_layout)

        # --- ComboBox Ano || Permite escolher outro ano, ao trocar -> chama on_combo_box_ano_changed
        self.combo_ano = QComboBox()
        mes_atual = hoje.month
        anos_para_exibir = [self.ano]
        if mes_atual >= 7:
            anos_para_exibir.append(self.ano + 1)
        for a in anos_para_exibir:
            self.combo_ano.addItem(str(a))
        self.combo_ano.setCurrentText(str(self.ano))
        self.combo_ano.currentTextChanged.connect(self.on_combo_ano_changed)
        pesquisa_layout.addWidget(QLabel("Ano:"))
        pesquisa_layout.addWidget(self.combo_ano)
        pesquisa_layout.addStretch()

        # --- Lista de nomes ---
        self.table_nomes.setRowCount(len(self.dados))
        self.labels_nomes.clear()
        self.row_por_nome.clear()

        # Inserir nomes na tabela de nomes || Coloca cada nome em uma linha || Guarda o mapeamento nome -> Linha
        for row_index, pessoa in enumerate(self.dados):
            nome = pessoa.get("nome", "Vazio")
            matricula = pessoa.get("matricula", "Vazio")
            afastado = pessoa.get("afastado", False)

            if afastado:
                nome_completo = f"** {nome} ({matricula})".strip()
            else:
                nome_completo = f"{nome} ({matricula})".strip()

            item = QTableWidgetItem(nome_completo)

            if afastado:
                item.setForeground(QColor("red"))

            item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            linha = row_index
            self.table_nomes.setItem(linha, 0, item)
            self.table_nomes.setRowHeight(linha, 30)
            self.row_por_nome[nome_completo] = [linha]

        # --- Cabeçalho (meses + dias) ---
        self.widget_cabecalho = QWidget()
        self.cabecalho_layout = QVBoxLayout(self.widget_cabecalho)
        self.cabecalho_layout.setContentsMargins(0, 0, 0, 0)
        self.cabecalho_layout.setSpacing(0)

        # --- Grade (células) ---
        self.widget_grade = QWidget()
        self.grade_layout = QVBoxLayout(self.widget_grade)
        self.grade_layout.setContentsMargins(0, 8, 0, 0)
        self.grade_layout.setSpacing(0)

        # Montagem
        self.montar_cabecalho()
        self.montar_grade()

        from PyQt6.QtWidgets import QScrollArea

        self.scroll_calendario = QScrollArea()
        self.scroll_calendario.setWidgetResizable(True)

        self.scroll_calendario.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        self.scroll_calendario.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_calendario.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_calendario.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        from PyQt6.QtWidgets import QScrollArea

        self.scroll_cabecalho = QScrollArea()
        self.scroll_cabecalho.setWidgetResizable(True)
        self.scroll_cabecalho.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_cabecalho.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.scroll_cabecalho.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_cabecalho.setFixedHeight(90)

        self.scroll_cabecalho.setWidget(self.widget_cabecalho)

        self.scroll_cabecalho.setSizePolicy(
            self.scroll_cabecalho.sizePolicy().horizontalPolicy(),
            self.scroll_cabecalho.sizePolicy().verticalPolicy(),
        )

        # ===============================
        # CONTAINER DO CALENDÁRIO (DIREITA)
        # ===============================

        self.calendario_container = QWidget()
        self.calendario_layout = QVBoxLayout(self.calendario_container)
        self.calendario_layout.setContentsMargins(0, 0, 0, 0)
        self.calendario_layout.setSpacing(0)

        # ===============================
        # TOPO ALINHADO (ESQ + DIR)
        # ===============================

        topo_layout = QHBoxLayout()
        topo_layout.setContentsMargins(0, 0, 0, 0)
        topo_layout.setSpacing(0)

        # --- TOPO ESQUERDO (pesquisa)
        topo_esquerda = QVBoxLayout()
        topo_esquerda.setContentsMargins(0, 0, 0, 0)
        layout_lider = QHBoxLayout()
        layout_lider.addWidget(self.label_lider)
        layout_lider.addWidget(self.combo_opcoes)
        layout_lider.addStretch()
        topo_esquerda.addLayout(layout_lider)
        topo_esquerda.addLayout(pesquisa_layout)

        topo_esquerda_container = QWidget()
        topo_esquerda_container.setLayout(topo_esquerda)
        topo_esquerda_container.setFixedWidth(320)

        # --- TOPO DIREITO (cabeçalho)
        topo_direita_container = QWidget()
        topo_direita_layout = QVBoxLayout(topo_direita_container)
        topo_direita_layout.setContentsMargins(0, 0, 0, 0)
        topo_direita_layout.setSpacing(0)

        topo_direita_layout.addWidget(
            self.scroll_cabecalho, alignment=Qt.AlignmentFlag.AlignBottom
        )

        # --- Junta esquerda + direita
        topo_layout.addWidget(topo_esquerda_container, 0)  # fixa esquerda
        topo_layout.addWidget(topo_direita_container, 1)  # direita expande

        # --- Scroll APENAS para a grade
        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.addWidget(self.widget_grade)

        self.scroll_calendario.setWidget(self.scroll_container)

        # --- Cabeçalho + scroll da grade
        self.calendario_layout.addWidget(self.scroll_calendario)

        layout_conteudo = QHBoxLayout()
        layout_conteudo.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_conteudo.addWidget(self.nomes_container, 0)
        layout_conteudo.addWidget(self.calendario_container, 1)

        layout_geral = QVBoxLayout(
            self
        )  # Layout vertical que organiza as coisas de cima para baixo
        layout_geral.addLayout(topo_layout)
        layout_geral.addLayout(
            layout_conteudo
        )  # Segundo o layout_conteudo, que contém: Tabela de nomes + pesquisa + combobox ano || Grade Calendário
        layout_geral.addWidget(manual_frame)  # Primeiro o Manual (Topo da tela)
        self.setLayout(layout_geral)
        self.carregando = False

        layout_geral.setContentsMargins(0, 0, 0, 0)
        layout_geral.setSpacing(0)

        self.sincronizar_scroll()
        
        QTimer.singleShot(100, self.ir_para_data_atual)
        
        


    # ------------------- Funções -------------------
    dados_alterados = pyqtSignal(list)

    def contar_ausencias_no_dia(self, mes, dia):
        return sum(
            1
            for item in self.dados_salvos
            if item.get("ano") == self.ano
            and item.get("mes") == mes
            and item.get("dia") == dia
            and item.get("valor")
        )
        
    def ir_para_data_atual(self):
        hoje = datetime.now()

        # Só faz isso se o calendário exibido for o ano atual
        if self.ano != hoje.year:
            return

        mes = hoje.month
        dia = hoje.day

        for col, (m, d) in enumerate(self.col_map):
            if m == mes and d == dia:
                pos_x = self.tabela.columnViewportPosition(col)
                self.tabela.horizontalScrollBar().setValue(pos_x)
                break

    def atualizar_totais_colunas(self):
        if not hasattr(self, "tabela") or self.tabela is None:
            return
        if not hasattr(self, "item_sem_por_col"):
            return
        if not hasattr(self, "col_map"):
            return

        dias_semana_pt = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

        for col, item_sem in self.item_sem_por_col.items():
            total = 0
            for row in range(self.tabela.rowCount()):
                w = self.tabela.cellWidget(row, col)
                if isinstance(w, QLineEdit) and (w.text() or "").strip():
                    total += 1

            mes, dia = self.col_map[col]
            dia_sem = calendar.weekday(self.ano, mes, dia)
            base = dias_semana_pt[dia_sem]

            item_sem.setText(f"{base}\n({total})" if total > 0 else base)
            item_sem.setToolTip(f"Total de ausências no dia: {total}")

    def sincronizar_scroll(self):
        try:
            # Vertical: nomes <-> grade (considera offset nas linhas fantasma)
            def sync_nomes_to_grade(value):
                # Ajusta valor considerando linhas fantasma ocultas
                self.tabela.verticalScrollBar().setValue(value)

            def sync_grade_to_nomes(value):
                self.table_nomes.verticalScrollBar().setValue(value)

            self.table_nomes.verticalScrollBar().valueChanged.connect(
                sync_nomes_to_grade
            )
            self.tabela.verticalScrollBar().valueChanged.connect(sync_grade_to_nomes)

            # Horizontal: cabeçalho <-> grade
            self.tabela_cabecalho.horizontalScrollBar().valueChanged.connect(
                self.tabela.horizontalScrollBar().setValue
            )
            self.tabela.horizontalScrollBar().valueChanged.connect(
                self.tabela_cabecalho.horizontalScrollBar().setValue
            )
        except Exception:
            pass

    def montar_cabecalho(self):
        import calendar
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
        from PyQt6.QtGui import QFont
        from PyQt6.QtCore import Qt
        
        hoje = datetime.now()

        # Limpa cabeçalho antigo
        for i in reversed(range(self.cabecalho_layout.count())):
            widget = self.cabecalho_layout.itemAt(i).widget()

            if widget is not None:
                widget.setParent(None)

        from PyQt6.QtWidgets import QAbstractItemView

        tabela = QTableWidget()
        tabela.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        tabela.setWordWrap(True)
        tabela.setTextElideMode(Qt.TextElideMode.ElideNone)  # tira os "..."
        tabela.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        tabela.setRowCount(3)

        meses_info = [(m, calendar.monthrange(self.ano, m)[1]) for m in range(1, 13)]
        total_colunas = sum(d for _, d in meses_info)
        tabela.setColumnCount(total_colunas)

        tabela.verticalHeader().setVisible(False)
        tabela.horizontalHeader().setVisible(False)
        tabela.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tabela.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Linha 0: meses
        col = 0
        for mes, dias in meses_info:
            item = QTableWidgetItem(self.meses_pt[mes])
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabela.setItem(0, col, item)
            tabela.setSpan(0, col, 1, dias)
            col += dias

        dias_semana_pt = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

        self.item_sem_por_col = {}

        col = 0
        for mes, dias in meses_info:
            for dia in range(1, dias + 1):
                dia_sem = calendar.weekday(self.ano, mes, dia)

                item_sem = QTableWidgetItem(dias_semana_pt[dia_sem])
                item_sem.setTextAlignment(
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
                )
                
                if self.ano == hoje.year and mes == hoje.month and dia == hoje.day:
                    item_sem.setForeground(QColor("#1976D2"))
                    item_sem.setToolTip("Hoje")

                tabela.setItem(1, col, item_sem)
                self.item_sem_por_col[col] = item_sem

                item_dia = QTableWidgetItem(str(dia))
                item_dia.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                fonte = QFont("Arial", 8)
                fonte.setBold(True)

                #  pega data atual
                hoje = datetime.now()

                # se for o dia atual
                if self.ano == hoje.year and mes == hoje.month and dia == hoje.day:
                    fonte.setBold(True)
                    fonte.setPointSize(10)  # deixa maior
                    item_dia.setForeground(QColor("#1976D2"))  # verde elegante
                    item_dia.setToolTip("Hoje")

                item_dia.setFont(fonte)

                tabela.setItem(2, col, item_dia)

                col += 1

        # Linha 1 e 2: dias da semana e números
        dias_semana_pt = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

        self.tabela_cabecalho = tabela
        self.cabecalho_layout.addWidget(self.tabela_cabecalho)
        # Coluna fantasma (alinhamento com nomes)

        # conteúdo do cabeçalho maior que a janela (pra existir scroll vertical)
        tabela.setMinimumHeight(93)
        tabela.setMaximumHeight(93)

        tabela.setRowHeight(0, 23)  # mês
        tabela.setRowHeight(1, 33)  # dia semana
        tabela.setRowHeight(2, 23)  # número

        tabela.setSizePolicy(
            tabela.sizePolicy().horizontalPolicy(), tabela.sizePolicy().verticalPolicy()
        )

    def montar_grade(self):
        import calendar
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QLineEdit
        from PyQt6.QtGui import QFont
        from PyQt6.QtCore import Qt

        # --- Limpa layout antigo antes de adicionar nova tabela ---
        for i in reversed(range(self.grade_layout.count())):
            widget = self.grade_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        tabela = QTableWidget()  # Cria a tabela da grade

        meses_info = [(m, calendar.monthrange(self.ano, m)[1]) for m in range(1, 13)]
        total_colunas = sum(d for (_, d) in meses_info)
        tabela.setRowCount(len(self.dados))

        # garante que a grade tenha a MESMA altura de linha da tabela de nomes
        ALTURA_LINHA = 30
        tabela.verticalHeader().setDefaultSectionSize(ALTURA_LINHA)

        for r in range(len(self.dados)):
            tabela.setRowHeight(r, ALTURA_LINHA)

        tabela.setColumnCount(total_colunas)
        tabela.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        tabela.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        tabela.verticalHeader().setVisible(False)
        tabela.horizontalHeader().setVisible(False)
        tabela.setShowGrid(True)

        # Mapeamento coluna -> (mes, dia)
        self.col_map = []
        for mes, dias in meses_info:
            for d in range(1, dias + 1):
                self.col_map.append((mes, d))

        self.col_map = self.col_map

        # Linhas de pessoas
        self.row_por_nome.clear()
        self.celulas.clear()

        for row_index, pessoa in enumerate(self.dados):

            nome_completo = (
                f"{pessoa.get('nome','Vazio')} ({pessoa.get('matricula','Vazio')})"
            )
            self.row_por_nome[nome_completo] = [row_index]
            self.linhas_por_nome[nome_completo] = []

            for c_index, (mes, dia) in enumerate(self.col_map):
                dia_sem = calendar.weekday(self.ano, mes, dia)
                cor_base = "lightgray" if dia_sem >= 5 else "white"
                entrada = QLineEdit()
                entrada.setFixedSize(30, 30)
                entrada.setAlignment(Qt.AlignmentFlag.AlignCenter)
                entrada.setMaxLength(1)
                entrada.setStyleSheet(
                    f"border:1px solid black; background-color:{cor_base};"
                )

                # Carrega valores salvos
                valor_salvo = next(
                    (
                        item["valor"]
                        for item in self.dados_salvos
                        if item.get("ano") == self.ano
                        and item.get("nome") == nome_completo
                        and item.get("mes") == mes
                        and item.get("dia") == dia
                    ),
                    "",
                )
                if valor_salvo:
                    letra = valor_salvo[-1:].upper()
                    if letra in self.cores_manual:
                        entrada.setText(letra)
                        entrada.setStyleSheet(
                            f"border:1px solid black; background-color:{self.cores_manual[letra]};"
                        )

                        # Se for F ou L, já vem bloqueado
                        if letra in self.codigos_bloqueados:
                            entrada.setReadOnly(True)

                    else:
                        entrada.setText("")

                # Handler de edição
                def criar_handler(
                    e, mes=mes, dia=dia, nome=nome_completo, cor_base=cor_base
                ):
                    def handler(texto):

                        if self.carregando:
                            return

                        letra = texto[-1:].upper() if texto else ""
                        
                        # Impede inserir F ou L manualmente
                        if letra in self.codigos_bloqueados:
                            e.blockSignals(True)
                            e.setText("")
                            e.setStyleSheet(
                                f"border:1px solid black; background-color:{cor_base};"
                            )
                            e.blockSignals(False)
                            return

                        # Atualiza visual
                        if letra in self.cores_manual:
                            e.blockSignals(True)
                            e.setText(letra)
                            e.setStyleSheet(
                                f"border:1px solid black; background-color:{self.cores_manual[letra]};"
                            )
                            e.blockSignals(False)
                        else:
                            e.blockSignals(True)
                            e.setText("")
                            e.setStyleSheet(
                                f"border:1px solid black; background-color:{cor_base};"
                            )
                            e.blockSignals(False)

                        # Remove item antigo
                        self.dados_salvos[:] = [
                            item
                            for item in self.dados_salvos
                            if not (
                                item["ano"] == self.ano
                                and item["nome"] == nome
                                and item["mes"] == mes
                                and item["dia"] == dia
                            )
                        ]

                        # Adiciona novo
                        if letra:
                            self.dados_salvos.append(
                                {
                                    "sigla": self.sigla,
                                    "ano": self.ano,
                                    "nome": nome,
                                    "mes": mes,
                                    "dia": dia,
                                    "valor": letra,
                                }
                            )

                        self.dados_alterados.emit(self.dados_salvos)
                        self.atualizar_totais_colunas()

                    return handler

                entrada.textChanged.connect(
                    criar_handler(
                        entrada, mes=mes, dia=dia, nome=nome_completo, cor_base=cor_base
                    )
                )
                tabela.setCellWidget(row_index, c_index, entrada)
                self.linhas_por_nome[nome_completo].append(entrada)
                self.celulas.append((nome_completo, mes, dia, entrada))

        # Ajustes finais
        for c in range(total_colunas):
            tabela.setColumnWidth(c, 33)

        self.tabela = tabela

        self.tabela.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabela.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.grade_layout.addWidget(self.tabela, 1)

        if hasattr(self, "tabela_cabecalho"):
            for col in range(self.tabela.columnCount()):
                largura = self.tabela.columnWidth(col)
                self.tabela_cabecalho.setColumnWidth(col, largura)

        self.atualizar_totais_colunas()

    def atualizar_dados(self, novos_dados):
        self.dados_salvos = novos_dados

        # guarda a posição atual do scroll horizontal do cabeçalho
        scroll_x = 0
        scroll_y = 0

        if hasattr(self, "tabela_cabecalho") and self.tabela_cabecalho is not None:
            scroll_x = self.tabela_cabecalho.horizontalScrollBar().value()

        if hasattr(self, "table_nomes") and self.table_nomes is not None:
            scroll_y = self.table_nomes.verticalScrollBar().value()

        # remove a tabela antiga
        if hasattr(self, "tabela") and self.tabela is not None:
            self.tabela.setParent(None)
            self.tabela.deleteLater()
            self.tabela = None

        # limpa widgets antigos do layout da grade
        for i in reversed(range(self.grade_layout.count())):
            w = self.grade_layout.itemAt(i).widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        # recria a grade
        self.montar_grade()
        self.sincronizar_scroll()

        # força o Qt a aplicar layout antes de restaurar scroll
        self.widget_grade.updateGeometry()
        self.scroll_container.updateGeometry()

        # restaura a posição correta do scroll
        if hasattr(self, "tabela") and self.tabela is not None:
            self.tabela.horizontalScrollBar().setValue(scroll_x)
            self.tabela.verticalScrollBar().setValue(scroll_y)

        if hasattr(self, "tabela_cabecalho") and self.tabela_cabecalho is not None:
            self.tabela_cabecalho.horizontalScrollBar().setValue(scroll_x)

        if hasattr(self, "table_nomes") and self.table_nomes is not None:
            self.table_nomes.verticalScrollBar().setValue(scroll_y)

        # ajuste final no próximo ciclo da UI
        QTimer.singleShot(0, lambda: self._ajustar_scroll_pos_consulta(scroll_x, scroll_y))
    
    def _ajustar_scroll_pos_consulta(self, scroll_x, scroll_y):
        if hasattr(self, "tabela") and self.tabela is not None:
            self.tabela.horizontalScrollBar().setValue(scroll_x)
            self.tabela.verticalScrollBar().setValue(scroll_y)
            self.tabela.viewport().update()

        if hasattr(self, "tabela_cabecalho") and self.tabela_cabecalho is not None:
            self.tabela_cabecalho.horizontalScrollBar().setValue(scroll_x)
            self.tabela_cabecalho.viewport().update()

        if hasattr(self, "table_nomes") and self.table_nomes is not None:
            self.table_nomes.verticalScrollBar().setValue(scroll_y)

    # Função que muda o ano.
    def on_combo_ano_changed(self, texto):
        try:
            self.ano = int(texto)
        except:
            return

        # REMOVER A GRADE ANTIGA COMPLETAMENTE ---
        if hasattr(self, "tabela") and self.tabela is not None:
            self.tabela.setParent(None)
            self.tabela.deleteLater()
            self.tabela = None

        # Remove também qualquer widget restante na grade
        for i in reversed(range(self.grade_layout.count())):
            w = self.grade_layout.itemAt(i).widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        # --- RECRIAR A GRADE NOVA ---
        self.montar_grade()  # cria self.tabela NOVA, limpa, sem conexões antigas

        # --- RECRIAR OS MAPEAMENTOS (linhas_por_nome e row_por_nome) ---
        self.linhas_por_nome.clear()
        for row_index, pessoa in enumerate(self.dados):
            nome_completo = (
                f"{pessoa.get('nome','Vazio')} ({pessoa.get('matricula','Vazio')})"
            )
            self.linhas_por_nome[nome_completo] = []
            for col in range(self.tabela.columnCount()):
                widget = self.tabela.cellWidget(row_index, col)
                if widget:
                    self.linhas_por_nome[nome_completo].append(widget)

        # --- RECRIAR A TABELA DE NOMES COM OFFSET ---
        self.table_nomes.clearContents()

        # Preenchendo nomes COM OFFSET
        self.row_por_nome.clear()
        for row_index, pessoa in enumerate(self.dados):
            nome_completo = f"{pessoa.get('nome','Vazio')} ({pessoa.get('matricula','Vazio')})".strip()
            item = QTableWidgetItem(nome_completo)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            linha = row_index
            self.table_nomes.setRowHeight(linha, 30)
            self.row_por_nome[nome_completo] = [linha]

        self.montar_cabecalho()

        self.sincronizar_scroll()
        self.atualizar_totais_colunas()
        
    def obter_lideres_equipe(self) -> list[str]:
        lideres = []
        vistos = set()

        for pessoa in self.dados:
            nome = (pessoa.get("nome") or "").strip()
            matricula = str(pessoa.get("matricula") or "").strip()
            funcao = (pessoa.get("funcao") or "").strip().upper()

            nome_completo = f"{nome} ({matricula})"

            if "LIDER DE EQUIPE" in funcao and nome_completo not in vistos:
                lideres.append(nome_completo)
                vistos.add(nome_completo)

        return lideres
    
    def filtrar_nomes(self, texto=""):
        texto = (texto or "").strip().lower()

        for i in range(len(self.dados)):
            item = self.table_nomes.item(i, 0)

            if not item:
                continue

            nome = item.text().lower()

            if texto == "":
                mostrar = True
            else:
                mostrar = nome.startswith(texto)

            self.table_nomes.setRowHidden(i, not mostrar)

            if hasattr(self, "tabela") and self.tabela is not None:
                self.tabela.setRowHidden(i, not mostrar)

        self.table_nomes.verticalScrollBar().setValue(0)

        if hasattr(self, "tabela") and self.tabela is not None:
            self.tabela.verticalScrollBar().setValue(0)
    
    def limpar_filtro(self):
        self.campo_pesquisa.blockSignals(True)
        self.campo_pesquisa.clear()
        self.campo_pesquisa.blockSignals(False)

        self.filtrar_nomes("")

    def obter_nomes(self) -> list[str]:
        """
        Retorna TODOS os nomes do sistema (não depende de filtro),
        no mesmo formato usado no JSON: "Nome (matricula)".
        """
        nomes = []
        for pessoa in self.dados:
            nome = (pessoa.get("nome") or "").strip()
            matricula = str(pessoa.get("matricula") or "").strip()
            nomes.append(f"{nome} ({matricula})")
        return nomes
    
    def set_caminho_json(self, caminho_json: str | Path):
        self.caminho_json = str(caminho_json)


