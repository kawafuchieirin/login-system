"""Passkey (WebAuthn) endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_current_user
from models.auth import TokenResponse
from models.passkey import (
    PasskeyAuthenticationOptionsRequest,
    PasskeyAuthenticationVerifyRequest,
    PasskeyCredentialListResponse,
    PasskeyCredentialResponse,
    PasskeyRegistrationVerifyRequest,
)
from services.auth_service import create_access_token, get_user_by_id
from services.passkey_service import (
    create_authentication_options,
    create_registration_options,
    delete_credential,
    list_credentials,
    verify_authentication,
    verify_registration,
)

router = APIRouter(prefix="/api/v1/passkey", tags=["passkey"])


@router.post("/register/options")
async def registration_options(
    user_id: str = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    """Get WebAuthn registration options. Requires authentication."""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return create_registration_options(user_id, user["email"])


@router.post("/register/verify")
async def registration_verify(
    body: PasskeyRegistrationVerifyRequest,
    user_id: str = Depends(get_current_user),  # noqa: B008
) -> PasskeyCredentialResponse:
    """Verify WebAuthn registration response."""
    try:
        result = verify_registration(user_id, body.credential)
    except (ValueError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return PasskeyCredentialResponse(**result)


@router.post("/authenticate/options")
async def authentication_options(
    body: PasskeyAuthenticationOptionsRequest,
) -> dict[str, Any]:
    """Get WebAuthn authentication options. No authentication required."""
    result = create_authentication_options(body.email)
    return result


@router.post("/authenticate/verify")
async def authentication_verify(
    body: PasskeyAuthenticationVerifyRequest,
) -> TokenResponse:
    """Verify WebAuthn authentication response and return JWT."""
    challenge_user_id = body.credential.get("_challenge_user_id", "")
    # Remove internal field before passing to verification
    credential = {k: v for k, v in body.credential.items() if k != "_challenge_user_id"}

    try:
        user_id = verify_authentication(credential, challenge_user_id)
    except (ValueError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e

    token = create_access_token(user_id)
    return TokenResponse(access_token=token)


@router.get("/credentials")
async def get_credentials(
    user_id: str = Depends(get_current_user),  # noqa: B008
) -> PasskeyCredentialListResponse:
    """List all passkey credentials for the current user."""
    credentials = list_credentials(user_id)
    return PasskeyCredentialListResponse(credentials=[PasskeyCredentialResponse(**c) for c in credentials])


@router.delete("/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_credential(
    credential_id: str,
    user_id: str = Depends(get_current_user),  # noqa: B008
) -> None:
    """Delete a passkey credential."""
    deleted = delete_credential(user_id, credential_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
