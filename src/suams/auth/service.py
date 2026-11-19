"""Authentication business logic service."""
from sqlalchemy.orm import Session
from suams.auth.security import verify_password, create_access_token
from suams.models.user import User, UserRole
from suams.schemas.auth import Token


class AuthService:
    """Service providing user authentication and token creation operations."""

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> User | None:
        """Authenticate user against database records.

        Args:
            db: SQLAlchemy session.
            username: Provided username.
            password: Provided plaintext password.

        Returns:
            The User instance if credentials match and user is active, else None.
        """
        user: User | None = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_user_token(user: User) -> Token:
        """Generate access token for an authenticated user.

        Args:
            user: Authenticated User model instance.

        Returns:
            A Token schema instance containing the JWT access token and metadata.
        """
        role_value = user.role.value if isinstance(user.role, UserRole) else str(user.role)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "role": role_value,
            }
        )
        return Token(
            access_token=access_token,
            token_type="bearer",
            role=role_value,
            user_id=user.id,
        )
