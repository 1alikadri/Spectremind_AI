from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
REPORTS_DIR = DATA_DIR / "reports"

LLM_API_BASE = os.getenv("LLM_API_BASE", "http://127.0.0.1:1234/v1")
LLM_CHAT_COMPLETIONS_PATH = os.getenv("LLM_CHAT_COMPLETIONS_PATH", "/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "local-model")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
INTENT_ROUTER_ENABLED = os.getenv("INTENT_ROUTER_ENABLED", "1").strip().lower() in {
    "1", "true", "yes", "on"
}
INTENT_ROUTER_MODEL = os.getenv("INTENT_ROUTER_MODEL", LLM_MODEL)
INTENT_ROUTER_TIMEOUT_SECONDS = int(os.getenv("INTENT_ROUTER_TIMEOUT_SECONDS", "30"))

for folder in [DATA_DIR, SESSIONS_DIR, REPORTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)