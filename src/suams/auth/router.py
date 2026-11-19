"""Authentication API router for login and token issuance."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from suams.auth.dependencies import get_current_user
from suams.auth.service import AuthService
from suams.database import get_db
from suams.models.user import User
from suams.schemas.auth import LoginRequest, Token
from suams.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate credentials and issue a signed JWT access token.

    Returns:
        Token schema with bearer token and role.

    Raises:
        HTTPException (401): If credentials are invalid.
    """
    user = AuthService.authenticate_user(
        db=db,
        username=login_data.username,
        password=login_data.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthService.create_user_token(user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the profile of the currently authenticated user."""
    return current_user
