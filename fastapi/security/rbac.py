from models.user import User
from security.auth import get_current_user

from fastapi import Depends, HTTPException, status


class RoleChecker:
    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        user: User = Depends(get_current_user),
    ) -> User:
        if not set(user.user_roles).intersection(self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You don't have permission to access this action.",
            )

        return user
