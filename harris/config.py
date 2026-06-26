import sys
import tomllib
import tomli_w
import typer
from pathlib import Path

CONFIG_DIR = Path.home() / ".harris"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "rb") as f:
        return tomllib.load(f)


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(config, f)


def get_account(name: str) -> dict:
    accounts = load_config().get("accounts", {})
    if name not in accounts:
        raise typer.BadParameter(
            f"账号 '{name}' 不存在，请先运行: harris auth setup --account {name}"
        )
    return accounts[name]


def list_accounts() -> list[str]:
    return list(load_config().get("accounts", {}).keys())


def save_account(name: str, account_config: dict) -> None:
    config = load_config()
    config.setdefault("accounts", {})[name] = account_config
    save_config(config)


def delete_account(name: str) -> None:
    config = load_config()
    config.get("accounts", {}).pop(name, None)
    save_config(config)


def get_server_url() -> str:
    import os
    if url := os.environ.get("HARRIS_SERVER_URL"):
        return url.rstrip("/")
    config = load_config()
    return config.get("server", {}).get("url", "http://localhost:8000").rstrip("/")


def load_session() -> dict:
    session_file = CONFIG_DIR / "session.json"
    if not session_file.exists():
        return {}
    import json
    with open(session_file) as f:
        return json.load(f)


def save_session(session: dict) -> None:
    import json
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    session_file = CONFIG_DIR / "session.json"
    with open(session_file, "w") as f:
        json.dump(session, f, indent=2)
    session_file.chmod(0o600)


def delete_session() -> None:
    session_file = CONFIG_DIR / "session.json"
    if session_file.exists():
        session_file.unlink()
