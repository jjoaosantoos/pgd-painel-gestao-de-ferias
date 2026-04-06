import sys
import json
from pathlib import Path

meses_pt = [
    "",
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


def get_app_dir() -> Path:
    """Pasta onde o app/exe está rodando."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()
SETTINGS_PATH = APP_DIR / "settings.json"  # guarda a pasta escolhida


def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_settings(cfg: dict) -> None:
    SETTINGS_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_output_dir() -> Path | None:
    """Retorna a pasta escolhida pelo usuário (se já existir e for válida)."""
    cfg = load_settings()
    raw = cfg.get("output_dir")
    if raw and Path(raw).exists():
        return Path(raw)
    return None


def set_output_dir(folder: str | Path) -> Path:
    """Define a pasta escolhida e persiste em settings.json."""
    folder = Path(folder)
    cfg = load_settings()
    cfg["output_dir"] = str(folder)
    save_settings(cfg)
    return folder


def build_paths(base_dir: Path, sigla: str) -> dict:
    """
    Cria subpastas dentro da pasta escolhida e devolve os caminhos.
    - FeriasJson/ferias_<SIGLA>.json (Salvar/Consultar)
    - exports/*.csv (Exportar)
    """
    base_dir = Path(base_dir)

    # normaliza sigla pra evitar "serd", "SERD ", etc
    sigla_norm = (sigla or "").strip().upper() or "SEM_SIGLA"

    pasta_exports = base_dir / "exports"
    pasta_exports.mkdir(parents=True, exist_ok=True)


    return {
        "base_dir": base_dir,
        "pasta_exports": pasta_exports,
        "sigla": sigla_norm,
    }
