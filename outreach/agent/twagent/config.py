"""Load secrets from .env and behavior from config.yaml into one Settings object."""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

AGENT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = AGENT_DIR / "config.yaml"
CONTEXT_PATH = AGENT_DIR / "context" / "PRODUCT.md"
DATA_PATH = AGENT_DIR / "data" / "queue.json"


@dataclass
class Caps:
    replies_per_day: int = 10
    posts_per_day: int = 4
    dms_per_day: int = 5

    def for_kind(self, kind: str) -> int:
        return {"reply": self.replies_per_day, "post": self.posts_per_day, "dm": self.dms_per_day}[kind]


@dataclass
class Settings:
    # LLM
    llm_model: str = "gpt-4o"
    llm_api_base: str | None = None
    llm_api_key: str | None = None
    # X credentials
    x_bearer_token: str | None = None
    x_api_key: str | None = None
    x_api_secret: str | None = None
    x_access_token: str | None = None
    x_access_token_secret: str | None = None
    # Behavior
    keywords: list[str] = field(default_factory=list)
    relevance_threshold: int = 7
    scan_max_tweets: int = 25
    caps: Caps = field(default_factory=Caps)
    voice_notes: str = ""
    min_send_gap_seconds: int = 45
    max_send_gap_seconds: int = 120


def load_settings() -> Settings:
    load_dotenv(AGENT_DIR / ".env")
    s = Settings()

    s.llm_model = os.getenv("LLM_MODEL", s.llm_model)
    s.llm_api_base = os.getenv("LLM_API_BASE")
    s.llm_api_key = os.getenv("LLM_API_KEY")
    s.x_bearer_token = os.getenv("X_BEARER_TOKEN")
    s.x_api_key = os.getenv("X_API_KEY")
    s.x_api_secret = os.getenv("X_API_SECRET")
    s.x_access_token = os.getenv("X_ACCESS_TOKEN")
    s.x_access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

    if CONFIG_PATH.exists():
        cfg = yaml.safe_load(CONFIG_PATH.read_text()) or {}
        s.keywords = cfg.get("keywords", s.keywords)
        s.relevance_threshold = cfg.get("relevance_threshold", s.relevance_threshold)
        s.scan_max_tweets = cfg.get("scan_max_tweets", s.scan_max_tweets)
        s.voice_notes = cfg.get("voice_notes", s.voice_notes)
        s.min_send_gap_seconds = cfg.get("min_send_gap_seconds", s.min_send_gap_seconds)
        s.max_send_gap_seconds = cfg.get("max_send_gap_seconds", s.max_send_gap_seconds)
        caps = cfg.get("daily_caps", {})
        s.caps = Caps(
            replies_per_day=caps.get("replies", s.caps.replies_per_day),
            posts_per_day=caps.get("posts", s.caps.posts_per_day),
            dms_per_day=caps.get("dms", s.caps.dms_per_day),
        )
    return s


def load_context_doc() -> str:
    if not CONTEXT_PATH.exists():
        raise FileNotFoundError(
            f"Context document not found at {CONTEXT_PATH}. "
            "Write context/PRODUCT.md first — it is the agent's entire understanding of what you're doing."
        )
    text = CONTEXT_PATH.read_text().strip()
    if len(text) < 100 or "REPLACE EVERYTHING BELOW" in text:
        raise ValueError(
            f"{CONTEXT_PATH} is still the template. "
            "Fill it in with your product, ICP, voice, and call-to-action before running the agent."
        )
    return text
