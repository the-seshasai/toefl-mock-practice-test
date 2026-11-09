from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-lite-latest"
    anthropic_api_key: str = ""
    claude_model: str = "claude-haiku-5-5"

    backend_port: int = 8001
    frontend_origin: str = "http://localhost:5173"

    data_dir: Path = Path("./data")
    whisper_model: str = "base"
    piper_voice_dir: Path = Path("./data/piper")

    @property
    def database_url(self) -> str:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(self.data_dir / 'toefl.db').resolve()}"


settings = Settings()
