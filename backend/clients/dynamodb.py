"""DynamoDB client and settings."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBServiceResource


class Settings(BaseSettings):
    """Application settings."""

    dynamodb_endpoint_url: str | None = None
    users_table_name: str = "login-system-users"
    todos_table_name: str = "login-system-todos"
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    cors_origins: str = "http://localhost:5173"
    debug: bool = False
    webauthn_rp_id: str = "localhost"
    webauthn_rp_name: str = "Login System"
    webauthn_origin: str = "http://localhost:5173"
    webauthn_credentials_table_name: str = "login-system-webauthn-credentials"
    auth_challenges_table_name: str = "login-system-auth-challenges"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_dynamodb_resource() -> DynamoDBServiceResource:
    """Get DynamoDB resource."""
    settings = get_settings()
    kwargs: dict[str, Any] = {"region_name": "ap-northeast-1"}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url
    return boto3.resource("dynamodb", **kwargs)
