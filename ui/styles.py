from pathlib import Path


def load_stylesheet() -> str:
    qss_path = Path(__file__).parent / "styles" / "app.qss"
    return qss_path.read_text(encoding="utf-8")


def asset_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / name
