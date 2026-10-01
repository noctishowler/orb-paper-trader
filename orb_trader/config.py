from pathlib import Path
import os
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    load_dotenv(ROOT / ".env")

    with open(ROOT / "config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        raise RuntimeError(
            "Missing Alpaca credentials. Copy .env.example to .env "
            "and add PAPER API credentials."
        )

    if config.get("paper") is not True:
        raise RuntimeError(
            "V1 is intentionally paper-only. config.yaml must contain paper: true"
        )

    config["alpaca"] = {
        "api_key": api_key,
        "secret_key": secret_key,
    }

    return config
