"""Passkey (WebAuthn) service."""

from __future__ import annotations

import base64
import json
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import (
    options_to_json,
    parse_authentication_credential_json,
    parse_registration_credential_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from clients.dynamodb import get_dynamodb_resource, get_settings


def _b64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    """Base64url decode with padding."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def _options_to_dict(options: Any) -> dict[str, Any]:
    """Convert webauthn options to JSON-serializable dict."""
    json_str: str = options_to_json(options)
    result: dict[str, Any] = json.loads(json_str)
    return result


def create_registration_options(user_id: str, email: str) -> dict[str, Any]:
    """Generate WebAuthn registration options."""
    settings = get_settings()

    # Get existing credentials for this user
    existing_credentials = _get_user_credentials(user_id)
    exclude_credentials = [
        PublicKeyCredentialDescriptor(id=_b64url_decode(cred["credential_id"])) for cred in existing_credentials
    ]

    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=user_id.encode(),
        user_name=email,
        user_display_name=email,
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )

    # Store challenge
    challenge_b64 = _b64url_encode(options.challenge)
    _store_challenge(user_id, challenge_b64, "register")

    return _options_to_dict(options)


def verify_registration(user_id: str, credential: dict[str, Any]) -> dict[str, str]:
    """Verify WebAuthn registration response and store credential."""
    settings = get_settings()

    # Get stored challenge
    challenge_b64 = _get_and_delete_challenge(user_id, "register")
    if not challenge_b64:
        raise ValueError("No registration challenge found or challenge expired")

    credential_json = json.dumps(credential)
    parsed = parse_registration_credential_json(credential_json)

    verification = verify_registration_response(
        credential=parsed,
        expected_challenge=_b64url_decode(challenge_b64),
        expected_rp_id=settings.webauthn_rp_id,
        expected_origin=settings.webauthn_origin,
    )

    # Store credential
    credential_id = _b64url_encode(verification.credential_id)
    public_key = _b64url_encode(verification.credential_public_key)
    now = datetime.now(UTC).isoformat()

    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.webauthn_credentials_table_name)
    table.put_item(
        Item={
            "pk": f"USER#{user_id}",
            "sk": f"CRED#{credential_id}",
            "credential_id": credential_id,
            "public_key": public_key,
            "sign_count": verification.sign_count,
            "created_at": now,
            "user_id": user_id,
        }
    )

    return {"credential_id": credential_id, "created_at": now}


def create_authentication_options(email: str | None = None) -> dict[str, Any]:
    """Generate WebAuthn authentication options."""
    settings = get_settings()

    allow_credentials: list[PublicKeyCredentialDescriptor] = []
    user_id: str | None = None

    if email:
        # Find user by email and get their credentials
        user = _get_user_by_email(email)
        if user:
            user_id = str(user["user_id"])
            credentials = _get_user_credentials(user_id)
            allow_credentials = [
                PublicKeyCredentialDescriptor(id=_b64url_decode(cred["credential_id"])) for cred in credentials
            ]

    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        allow_credentials=allow_credentials if allow_credentials else None,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    challenge_b64 = _b64url_encode(options.challenge)
    # Store challenge with a temporary ID (will match by challenge value)
    challenge_user_id = user_id or f"anonymous-{uuid.uuid4()}"
    _store_challenge(challenge_user_id, challenge_b64, "authenticate")

    result = _options_to_dict(options)
    result["_challenge_user_id"] = challenge_user_id
    return result


def verify_authentication(credential: dict[str, Any], challenge_user_id: str) -> str:
    """Verify WebAuthn authentication response. Returns user_id."""
    settings = get_settings()

    challenge_b64 = _get_and_delete_challenge(challenge_user_id, "authenticate")
    if not challenge_b64:
        raise ValueError("No authentication challenge found or challenge expired")

    # Find credential in database
    credential_id_b64 = credential.get("id", "")
    stored = _find_credential_by_id(credential_id_b64)
    if not stored:
        raise ValueError("Credential not found")

    credential_json = json.dumps(credential)
    parsed = parse_authentication_credential_json(credential_json)

    verification = verify_authentication_response(
        credential=parsed,
        expected_challenge=_b64url_decode(challenge_b64),
        expected_rp_id=settings.webauthn_rp_id,
        expected_origin=settings.webauthn_origin,
        credential_public_key=_b64url_decode(str(stored["public_key"])),
        credential_current_sign_count=int(stored["sign_count"]),
    )

    # Update sign count
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.webauthn_credentials_table_name)
    table.update_item(
        Key={"pk": stored["pk"], "sk": stored["sk"]},
        UpdateExpression="SET sign_count = :sc",
        ExpressionAttributeValues={":sc": verification.new_sign_count},
    )

    return str(stored["user_id"])


def list_credentials(user_id: str) -> list[dict[str, str]]:
    """List all passkey credentials for a user."""
    credentials = _get_user_credentials(user_id)
    return [{"credential_id": str(c["credential_id"]), "created_at": str(c["created_at"])} for c in credentials]


def delete_credential(user_id: str, credential_id: str) -> bool:
    """Delete a passkey credential."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.webauthn_credentials_table_name)

    response = table.delete_item(
        Key={"pk": f"USER#{user_id}", "sk": f"CRED#{credential_id}"},
        ReturnValues="ALL_OLD",
    )
    return bool(response.get("Attributes"))


# --- Helper functions ---


def _get_user_credentials(user_id: str) -> list[dict[str, Any]]:
    """Get all WebAuthn credentials for a user."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.webauthn_credentials_table_name)

    response = table.query(
        KeyConditionExpression="pk = :pk AND begins_with(sk, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": f"USER#{user_id}",
            ":sk_prefix": "CRED#",
        },
    )
    return list(response["Items"])


def _find_credential_by_id(credential_id: str) -> dict[str, Any] | None:
    """Find a credential by credential_id across all users."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.webauthn_credentials_table_name)

    # Scan for credential_id (not ideal but credentials table is small)
    response = table.scan(
        FilterExpression="credential_id = :cid",
        ExpressionAttributeValues={":cid": credential_id},
    )
    items = response["Items"]
    if not items:
        return None
    return dict(items[0])


def _get_user_by_email(email: str) -> dict[str, Any] | None:
    """Get user by email from users table."""
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
    return dict(response["Items"][0])


def _store_challenge(user_id: str, challenge: str, challenge_type: str) -> None:
    """Store a challenge in DynamoDB with TTL."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.auth_challenges_table_name)

    challenge_id = str(uuid.uuid4())
    ttl = int(time.time()) + 300  # 5 minutes

    table.put_item(
        Item={
            "pk": f"CHALLENGE#{challenge_id}",
            "user_id": user_id,
            "challenge": challenge,
            "type": challenge_type,
            "expires_at": ttl,
        }
    )


def _get_and_delete_challenge(user_id: str, challenge_type: str) -> str | None:
    """Get and delete a challenge for a user."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.auth_challenges_table_name)

    # Scan for user's challenge (small table with TTL)
    response = table.scan(
        FilterExpression="user_id = :uid AND #t = :type",
        ExpressionAttributeNames={"#t": "type"},
        ExpressionAttributeValues={
            ":uid": user_id,
            ":type": challenge_type,
        },
    )
    items = response["Items"]
    if not items:
        return None

    # Get the most recent challenge
    item = items[-1]
    challenge = str(item["challenge"])

    # Delete it
    table.delete_item(Key={"pk": item["pk"]})

    # Check expiry
    if int(str(item.get("expires_at", 0))) < int(time.time()):
        return None

    return challenge
