"""Application configuration loaded from environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


def _env(name, default=None):
    return os.getenv(name, default)


class Settings:
    def __init__(self):
        self.APP_NAME = "Network Privacy Monitoring & Communication Transparency Dashboard"
        self.API_HOST = _env("API_HOST", "127.0.0.1")
        self.API_PORT = int(_env("API_PORT", "8000"))
        self.LOG_LEVEL = _env("LOG_LEVEL", "INFO")
        self.LOG_FILE = Path(_env("LOG_FILE", str(BASE_DIR / "logs" / "application.log")))

        db_url = _env("DATABASE_URL", "sqlite:///./database/network_privacy.db")
        if db_url.startswith("sqlite:///"):
            # Resolve relative SQLite paths against the project root so the
            # database is created in the same place regardless of CWD.
            raw = db_url.replace("sqlite:///", "", 1)
            if not Path(raw).is_absolute():
                db_url = f"sqlite:///{(BASE_DIR / raw).as_posix()}"
        self.DATABASE_URL = db_url

        self.CAPTURE_INTERFACE = _env("CAPTURE_INTERFACE", "")
        self.RETENTION_DAYS = int(_env("RETENTION_DAYS", "30"))
        self.FLOW_TIMEOUT_SECONDS = int(_env("FLOW_TIMEOUT_SECONDS", "60"))
        self.FLUSH_INTERVAL_SECONDS = float(_env("FLUSH_INTERVAL_SECONDS", "2"))
        # DNS mappings expire quickly because IP→domain reuse is common; keeping
        # them short-lived avoids attributing traffic to the wrong site.
        self.DNS_CACHE_TTL_SECONDS = int(_env("DNS_CACHE_TTL_SECONDS", "300"))
        # Minimum interval between individual flow WebSocket events. Full live
        # snapshots are still broadcast every FLUSH_INTERVAL_SECONDS.
        self.WS_MIN_INTERVAL_SECONDS = float(_env("WS_MIN_INTERVAL_SECONDS", "1.0"))
        self.CORS_ORIGINS = [
            origin.strip()
            for origin in _env("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
            if origin.strip()
        ]
        self.DEMO_MODE = _env("DEMO_MODE", "false").lower() in ("1", "true", "yes")
        self.DEMO_TICK_SECONDS = float(_env("DEMO_TICK_SECONDS", "1.5"))

        self.REPORT_DIR = Path(_env("REPORT_DIR", str(BASE_DIR / "reports")))
        self.REPORT_DIR.mkdir(parents=True, exist_ok=True)

        self.SCORE_WEIGHTS = {
            "encryption": float(_env("WEIGHT_ENCRYPTION", "60")),
            "protocol": float(_env("WEIGHT_PROTOCOL", "20")),
            "unencrypted_penalty": float(_env("WEIGHT_UNENCRYPTED", "20")),
        }

        self.DATABASE_DIR = Path(_env("DATABASE_DIR", str(BASE_DIR / "database")))
        self.DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    def get_db_path(self):
        if self.DATABASE_URL.startswith("sqlite:///"):
            raw = self.DATABASE_URL.replace("sqlite:///", "", 1)
            if raw.startswith("./"):
                return self.DATABASE_DIR / raw[2:]
            return Path(raw)
        return None


settings = Settings()
