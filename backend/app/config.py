from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")  # one .env at the repo root, wherever the server starts

    # LLM: local Claude Code (`claude -p`), using the user's own Claude Code login. No API keys.
    claude_path: str = "claude"
    claude_model: str = ""  # e.g. haiku | sonnet; empty = Claude Code's default
    llm_min_interval_seconds: float = 0.0
    llm_max_retries: int = 2
    llm_timeout_seconds: float = 120.0

    frontend_origin: str = "http://localhost:5173"

    data_dir: Path = REPO_ROOT / "data"
    whisper_model: str = "base.en"  # directory name under whisper_dir
    whisper_dir: Path = REPO_ROOT / "data" / "whisper"
    piper_voice_dir: Path = REPO_ROOT / "data" / "piper"

    @property
    def recordings_dir(self) -> Path:
        return self.data_dir / "recordings"

    @property
    def audio_dir(self) -> Path:
        return self.data_dir / "audio"

    @property
    def database_url(self) -> str:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(self.data_dir / 'toefl.db').resolve()}"


settings = Settings()
