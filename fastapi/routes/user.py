from database import get_session
from models.user import GetUserResponse, User, UserRole
from security.rbac import RoleChecker
from sqlmodel import Session, select

from fastapi import APIRouter, Depends

user_router = APIRouter(prefix="/users", tags=["User"])

allow_read_users = RoleChecker([UserRole.ADMIN.name.lower()])


@user_router.get(
    "", dependencies=[Depends(allow_read_users)], response_model=list[GetUserResponse]
)
async def get_users(
    session: Session = Depends(get_session),
):
    users = session.exec(select(User)).all()

    return users
