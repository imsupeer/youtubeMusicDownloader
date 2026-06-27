from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YTDLP_")

    host: str = "127.0.0.1"
    port: int = 8765
    default_outdir: Path = Path.home() / "Downloads"
    default_bitrate: int = 192
    cookies_browser: str | None = None


settings = Settings()
