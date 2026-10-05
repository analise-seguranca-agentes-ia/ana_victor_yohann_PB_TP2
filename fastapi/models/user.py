import uuid
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr
from sqlmodel import JSON, Column, Field, SQLModel

UserRole = Enum("UserRole", [("DEFAULT", 0), ("ADMIN", 1)])


class User(SQLModel, table=True):
    user_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        unique=True,
        primary_key=True,
    )
    username: str = Field(index=True, unique=True)
    user_roles: list[str] = Field(
        default=[UserRole.DEFAULT.name], sa_column=Column(JSON)
    )
    email: EmailStr | None = Field(default=None, unique=True)
    full_name: str | None = Field(default=None)
    hashed_password: str


class GetUserResponse(BaseModel):
    username: str
    email: EmailStr | None = None
    full_name: str | None


class PostUserLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str


class PostUserRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str
