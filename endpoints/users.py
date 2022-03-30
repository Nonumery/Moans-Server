import os
import secrets
from typing import List
from fastapi import APIRouter, Depends
from core.config import MAIN_URL
from core.errors import EMAIL_EXC, PASS_EXC
from core.security import create_access_token, verify_password
from core.send import password_recovery
from db.tables import UserTable
from models.token import Token
from repositories.users import UserRepository
from .depends import get_current_user, get_session, get_user_repository
from models.users import User, UserChange, UserIn
from sqlalchemy.ext.asyncio import AsyncSession
router = APIRouter()  
    
@router.get("/", response_model=List[User], response_model_exclude=["hash_password"])
async def read_users(
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session),
    limit: int = 10, 
    skip: int = 0):
    return await users.get_users(session=session, limit=limit, skip=skip)

@router.post("/", response_model=User, response_model_exclude=["hash_password"])
async def create_user(
    user: UserIn,
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session)):
    c_user = await users.get_user_by_email(session, user.email)
    if c_user:
        raise EMAIL_EXC
    new_user = await users.add_user(session=session, email=user.email, password=user.password)
    if new_user:
        user_folder = f"tracks/user_{new_user.id}"
        if not os.path.isdir(user_folder):
            os.mkdir(user_folder)
    return new_user

@router.patch("/", response_model=User, response_model_exclude=["hash_password"])
async def update_user(
    user: UserChange,
    users: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)):
    c_user = await users.get_user_by_email(session, current_user.email)
    if c_user is None or not verify_password(user.password, c_user.hash_password):
        raise PASS_EXC
    c_user = await users.get_user_by_email(session, user.email)
    if c_user is not None and c_user.email != current_user.email:
        raise EMAIL_EXC

    return await users.update_user(session, int(current_user.id), user.email, user.new_password)

@router.get("/recovery/{email}")
async def recover_user(
    email: str,
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session)):
    user = await users.get_user_by_email(session=session, email=email)
    if user:
        token = create_access_token({"sub": user.email})
        text = f'To recover your password, follow the link: {MAIN_URL}/users/recovery/{email}/{token}'
        password_recovery(to=email, text=text)


@router.get("/recovery/{email}/{token}")
async def recover_user(
    email: str,
    token: str,
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session)):
    user : User = get_current_user(users, session, token)
    if user.email == email:
        new_password = secrets.token_urlsafe(32)
        users.update_user(session, int(user.id), user.email, new_password)