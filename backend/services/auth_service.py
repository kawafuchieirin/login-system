"""Authentication service."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from clients.dynamodb import get_dynamodb_resource, get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(hours=settings.jwt_expire_hours)
    payload: dict[str, Any] = {"sub": user_id, "exp": expire}
    return str(jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm))


def decode_access_token(token: str) -> str | None:
    """Decode JWT and return user_id, or None if invalid."""
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        sub: str | None = payload.get("sub")
        return sub
    except JWTError:
        return None


def register_user(email: str, password: str) -> dict[str, str]:
    """Register a new user. Returns user dict. Raises ValueError if email exists."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.users_table_name)

    # Check if email already exists
    response = table.query(
        IndexName="email-index",
        KeyConditionExpression="email = :email",
        ExpressionAttributeValues={":email": email},
    )
    if response["Items"]:
        raise ValueError("Email already registered")

    user_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    item: dict[str, str] = {
        "pk": f"USER#{user_id}",
        "user_id": user_id,
        "email": email,
        "password_hash": hash_password(password),
        "created_at": now,
    }
    table.put_item(Item=item)
    return {"user_id": user_id, "email": email, "created_at": now}


def authenticate_user(email: str, password: str) -> dict[str, str] | None:
    """Authenticate user by email and password. Returns user dict or None."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.users_table_name)

    response = table.query(
        IndexName="email-index",
        KeyConditionExpression="email = :email",
        ExpressionAttributeValues={":email": email},
    )
    if not response["Items"]:
        return None

    user = response["Items"][0]
    if not verify_password(password, str(user["password_hash"])):
        return None

    return {"user_id": str(user["user_id"]), "email": str(user["email"]), "created_at": str(user["created_at"])}


def get_user_by_id(user_id: str) -> dict[str, str] | None:
    """Get user by user_id."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.users_table_name)

    response = table.get_item(Key={"pk": f"USER#{user_id}"})
    item = response.get("Item")
    if not item:
        return None
    return {"user_id": str(item["user_id"]), "email": str(item["email"]), "created_at": str(item["created_at"])}
