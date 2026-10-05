from datetime import timedelta

from database import get_session
from limiter import limiter
from models.auth import Token
from models.user import PostUserLoginRequest, PostUserRegisterRequest, User
from security.auth import (ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user,
                           create_access_token, get_hash_password, get_user)
from sqlmodel import Session

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/token", response_model=Token)
@limiter.limit("10/minute")
async def login_get_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> Token:
    user = authenticate_user(
        PostUserLoginRequest(username=form_data.username, password=form_data.password),
        session,
    )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    new_user: PostUserRegisterRequest = Body(),
    session: Session = Depends(get_session),
):
    found_user = get_user(new_user.username, session)

    if found_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username is already in use."
        )

    user: User = User(
        username=new_user.username, hashed_password=get_hash_password(new_user.password)
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return {"detail": "User was successfully created."}
