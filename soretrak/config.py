"""Project settings, read from the environment (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)   # .env wins over a stale system variable

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "soretrak_gtfs.db"
KNOWLEDGE_DIR = ROOT / "soretrak" / "knowledge"
PROMPTS_DIR = ROOT / "soretrak" / "prompts"

# LLM provider: "groq" (development) or "openai". The same OpenAI-compatible
# client serves both; only the URL and the key change.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq").lower()

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": os.environ.get("GROQ_API_KEY"),
        "model_router": "openai/gpt-oss-20b",
        "model_agent": "qwen/qwen3.8-27b",
    },
    "openai": {
        "base_url": None,
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "model_router": "gpt-4.1-mini",
        "model_agent": "gpt-4.1-mini",
    },
}

MODEL_ROUTER = os.environ.get("LLM_MODEL_ROUTER") or PROVIDERS[LLM_PROVIDER]["model_router"]
MODEL_AGENT = os.environ.get("LLM_MODEL_AGENT") or PROVIDERS[LLM_PROVIDER]["model_agent"]

LLM_TIMEOUT_SECONDS = 30
LLM_RETRIES = 2            # retries on 429 / 5xx
LLM_RETRY_DELAY_SECONDS = 1.0
LLM_MAX_WAIT_SECONDS = 60  # beyond this, give up rather than keep the user waiting
