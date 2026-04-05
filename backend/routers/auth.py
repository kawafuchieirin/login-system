"""Authentication router."""

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_current_user
from models.auth import LoginRequest, MessageResponse, RegisterRequest, TokenResponse, UserResponse
from services.auth_service import authenticate_user, create_access_token, get_user_by_id, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest) -> UserResponse:
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    try:
        user = register_user(request.email, request.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return UserResponse(**user)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest) -> TokenResponse:
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(user["user_id"])
    return TokenResponse(access_token=token)


@router.post("/logout", response_model=MessageResponse)
def logout(_user_id: str = Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
def me(user_id: str = Depends(get_current_user)) -> UserResponse:
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(**user)
