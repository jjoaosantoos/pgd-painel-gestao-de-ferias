# PGD - Painel de Gestão de Férias

Sistema desktop desenvolvido em Python com PyQt6 para gerenciamento de férias e ausências de colaboradores.

---

## 🚀 Funcionalidades

-  Visualização em formato de calendário anual
-  Registro de férias (F), licença (L) e outros eventos
-  Bloqueio de edição para dados importados (F e L)
-  Salvamento local em JSON por área (sigla)
-  Controle de versão dos dados
-  Integração com banco de dados PostgreSQL
-  Exportação de calendário para CSV
-  Tela de login com validação

---

## 🧱 Estrutura do Projeto

```bash
api/            # API para consulta de dados
automacao/      # Scripts de automação (Selenium / Datafone)
dados/          # Acesso a dados (JSON e banco)
services/       # Regras de negócio
ui/             # Interface gráfica (PyQt6)
utils/          # Funções auxiliares
main.py         # Ponto de entrada do sistema
config.py       # Configurações gerais
