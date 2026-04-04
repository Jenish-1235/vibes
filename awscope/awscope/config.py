from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

import boto3
from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = Path.home() / ".awscope"
CONFIG_FILE = CONFIG_DIR / "config.toml"


class ConfigError(Exception):
    pass


@dataclass
class AccountConfig:
    alias: str
    auth_type: str               # "profile" | "profile+role" | "ambient+role" | "static" | "sso"
    profile: str | None = None
    role_arn: str | None = None
    role_session_name: str = "awscope"
    external_id: str | None = None
    access_key_id: str | None = None
    secret_access_key: str | None = None
    session_token: str | None = None


def _infer_auth_type(data: dict) -> str:
    has_profile = bool(data.get("profile"))
    has_role = bool(data.get("role_arn"))
    has_keys = bool(data.get("access_key_id"))
    is_sso = data.get("auth_type") == "sso"

    if is_sso:
        return "sso"
    if has_keys:
        return "static"
    if has_profile and has_role:
        return "profile+role"
    if has_role:
        return "ambient+role"
    return "profile"


def load_config() -> list[AccountConfig]:
    if not CONFIG_FILE.exists():
        raise ConfigError(
            f"Config file not found: {CONFIG_FILE}\n"
            "Run 'awscope init' to add your first account."
        )
    with open(CONFIG_FILE, "rb") as f:
        data = tomllib.load(f)

    accounts_data = data.get("accounts", {})
    if not accounts_data:
        raise ConfigError("No accounts configured. Run 'awscope init'.")

    accounts = []
    for alias, entry in accounts_data.items():
        auth_type = _infer_auth_type(entry)
        accounts.append(AccountConfig(
            alias=alias,
            auth_type=auth_type,
            profile=entry.get("profile"),
            role_arn=entry.get("role_arn"),
            role_session_name=entry.get("role_session_name", "awscope"),
            external_id=entry.get("external_id"),
            access_key_id=entry.get("access_key_id"),
            secret_access_key=entry.get("secret_access_key"),
            session_token=entry.get("session_token"),
        ))
    return accounts


def build_session(account: AccountConfig) -> boto3.Session:
    if account.auth_type == "static":
        return boto3.Session(
            aws_access_key_id=account.access_key_id,
            aws_secret_access_key=account.secret_access_key,
            aws_session_token=account.session_token,
        )

    if account.auth_type in ("profile", "sso"):
        return boto3.Session(profile_name=account.profile)

    # profile+role or ambient+role — need to assume the role
    if account.auth_type == "profile+role":
        base = boto3.Session(profile_name=account.profile)
    else:  # ambient+role
        base = boto3.Session()

    assume_kwargs: dict = {
        "RoleArn": account.role_arn,
        "RoleSessionName": account.role_session_name,
    }
    if account.external_id:
        assume_kwargs["ExternalId"] = account.external_id

    creds = base.client("sts").assume_role(**assume_kwargs)["Credentials"]
    return boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )


def save_account(account: AccountConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    existing: dict = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            existing = tomllib.load(f)

    existing.setdefault("accounts", {})[account.alias] = _account_to_toml_dict(account)

    with open(CONFIG_FILE, "w") as f:
        f.write(_dict_to_toml(existing))


def _account_to_toml_dict(account: AccountConfig) -> dict:
    d: dict = {}
    if account.profile:
        d["profile"] = account.profile
    if account.role_arn:
        d["role_arn"] = account.role_arn
    if account.role_session_name != "awscope":
        d["role_session_name"] = account.role_session_name
    if account.external_id:
        d["external_id"] = account.external_id
    if account.access_key_id:
        d["access_key_id"] = account.access_key_id
    if account.secret_access_key:
        d["secret_access_key"] = account.secret_access_key
    if account.session_token:
        d["session_token"] = account.session_token
    if account.auth_type == "sso":
        d["auth_type"] = "sso"
    return d


def _dict_to_toml(data: dict) -> str:
    lines = []
    for section, entries in data.items():
        if isinstance(entries, dict):
            for key, value in entries.items():
                if isinstance(value, dict):
                    lines.append(f"\n[{section}.{key}]")
                    for k, v in value.items():
                        lines.append(f'{k} = "{v}"')
                else:
                    lines.append(f'{key} = "{value}"')
    return "\n".join(lines) + "\n"


def get_anthropic_settings() -> dict:
    return {
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "base_url": os.getenv("ANTHROPIC_BASE_URL") or None,
        "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
    }


def get_minio_settings() -> dict | None:
    endpoint = os.getenv("MINIO_ENDPOINT")
    if not endpoint:
        return None
    return {
        "endpoint_url": endpoint,
        "aws_access_key_id": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        "aws_secret_access_key": os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        "bucket": os.getenv("MINIO_BUCKET", "awscope-exports"),
    }


def get_dynamodb_settings() -> dict | None:
    endpoint = os.getenv("DYNAMODB_ENDPOINT")
    if not endpoint:
        return None
    return {"endpoint_url": endpoint}
