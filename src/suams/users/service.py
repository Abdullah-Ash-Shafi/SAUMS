"""User business logic service integrating UserDashboardFactory."""
from dataclasses import asdict
from typing import Any
from sqlalchemy.orm import Session

from suams.models.user import User
from suams.users.factory import UserDashboardFactory, BaseDashboardPayload


class UserService:
    """Service handling user profile and dashboard operations."""

    @staticmethod
    def get_user_dashboard(user: User, db: Session | None = None) -> dict[str, Any]:
        """Generate and serialize the role-specific dashboard using UserDashboardFactory.

        Args:
            user: Current authenticated user.
            db: Optional SQLAlchemy session to query additional context.

        Returns:
            Dictionary representation of the specialized dashboard payload.
        """
        dashboard_payload: BaseDashboardPayload = UserDashboardFactory.create_dashboard(user)
        # Convert dataclass to dictionary for JSON response
        data = asdict(dashboard_payload)
        # Convert Enum to string value if needed
        if hasattr(data.get("role"), "value"):
            data["role"] = data["role"].value
        return data
