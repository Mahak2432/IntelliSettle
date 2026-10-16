from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = API_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=API_ROOT / ".env", extra="ignore")

    # Google Cloud. On Cloud Run these come from the service account, so no keys are needed.
    gcp_project: str | None = None
    gcp_region: str = "asia-south1"
    vertex_location: str = "global"
    # Set only for local experiments with an AI Studio key instead of Vertex AI.
    gemini_api_key: str | None = None

    gemini_model: str = "gemini-3.5-flash"
    gemini_model_lite: str = "gemini-3.1-flash-lite"
    # Tried in order when a model is out of quota or overloaded.
    gemini_fallback_models: list[str] = ["gemini-3.7-flash", "gemini-3.5-flash-lite"]

    # live: call real services. record: call them and save responses. replay: only use saved responses.
    external_mode: Literal["live", "record", "replay"] = "live"
    recordings_dir: Path = API_ROOT / "tests" / "recordings"

    storage_backend: Literal["memory", "firestore"] = "memory"
    seed_dir: Path = REPO_ROOT / "data" / "seed"
    uploads_dir: Path = API_ROOT / ".uploads"
    storage_bucket: str | None = None

    allowed_origins: list[str] = ["http://localhost:3000"]
    # dev: trust the X-Dev-Uid header (local only). firebase: verify Firebase ID tokens.
    auth_mode: Literal["dev", "firebase"] = "dev"
    # Demo isolation: each browser session sees and is checked against only its own claims.
    # Turn off for real use, so duplicate and reused-photo checks span every farmer.
    demo_sandbox: bool = True

    @property
    def ai_enabled(self) -> bool:
        return bool(self.gemini_api_key or self.gcp_project)


@lru_cache
def get_settings() -> Settings:
    return Settings()
