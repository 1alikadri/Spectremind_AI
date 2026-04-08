from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
REPORTS_DIR = DATA_DIR / "reports"

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "local-model")

for folder in [DATA_DIR, SESSIONS_DIR, REPORTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)