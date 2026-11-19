"""FastAPI security dependencies for JWT extraction and Role-Based Access Control (RBAC)."""
from typing import Callable, Sequence
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from suams.auth.security import decode_access_token
from suams.database import get_db
from suams.models.user import User, UserRole

# HTTP Bearer scheme
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Dependency that extracts, decodes, and verifies the current authenticated user.

    Raises:
        HTTPException (401): If the token is missing, invalid, or expired, or user not found.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims: subject missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user: User | None = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def require_roles(*allowed_roles: UserRole | str) -> Callable[[User], User]:
    """Dependency factory that enforces Role-Based Access Control (RBAC).

    Args:
        *allowed_roles: Variable number of roles permitted to access the endpoint.

    Returns:
        A dependency callable that returns the current User if authorized,
        or raises HTTP 403 Forbidden.
    """
    normalized_allowed = {
        role.value if isinstance(role, UserRole) else str(role)
        for role in allowed_roles
    }

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_str = (
            current_user.role.value
            if isinstance(current_user.role, UserRole)
            else str(current_user.role)
        )
        if user_role_str not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Insufficient permissions. Requires one of {list(normalized_allowed)}",
            )
        return current_user

    return role_checker
