"""Passkey (WebAuthn) models."""

from pydantic import BaseModel


class PasskeyRegistrationOptionsRequest(BaseModel):
    """Request to get registration options (user must be authenticated)."""


class PasskeyRegistrationVerifyRequest(BaseModel):
    """Verify registration response from browser."""

    credential: dict  # type: ignore[type-arg]


class PasskeyAuthenticationOptionsRequest(BaseModel):
    """Request to get authentication options."""

    email: str | None = None


class PasskeyAuthenticationVerifyRequest(BaseModel):
    """Verify authentication response from browser."""

    credential: dict  # type: ignore[type-arg]


class PasskeyCredentialResponse(BaseModel):
    """Response for a passkey credential."""

    credential_id: str
    created_at: str


class PasskeyCredentialListResponse(BaseModel):
    """Response for listing passkey credentials."""

    credentials: list[PasskeyCredentialResponse]
