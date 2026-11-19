"""User API router for user profile and role-specific dashboard views."""
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from suams.auth.dependencies import get_current_user
from suams.database import get_db
from suams.models.user import User
from suams.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return the role-specific dashboard for the currently authenticated user.

    Uses UserDashboardFactory (Factory Pattern) to generate the customized payload.
    """
    return UserService.get_user_dashboard(user=current_user, db=db)


@router.get("/me")
def get_current_profile(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Return basic profile information for the authenticated user."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        "department": current_user.department,
        "semester": current_user.semester,
    }
