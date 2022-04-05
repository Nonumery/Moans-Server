import hashlib
import json
import os
import secrets
import shutil
from typing import List
from fastapi import APIRouter, Depends, Request
from core.config import CLIENT_ID, MAIN_URL
from core.errors import ACCESS_EXC, AUTH_EXC, CONFIRM_EXC, EMAIL_EXC, PASS_EXC, TOKEN_EXC
from core.security import create_access_token, verify_password
from core.send import confirm_email, password_recovery
from repositories.users import UserRepository
from .depends import get_current_user, get_session, get_user_email, get_user_repository
from models.users import User, UserChange, UserIn
from sqlalchemy.ext.asyncio import AsyncSession
router = APIRouter()  
    
@router.get("/", response_model=List[User], response_model_exclude=["hash_password", "update_token"])
async def read_users(
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session),
    limit: int = 10, 
    skip: int = 0):
    return await users.get_users(session=session, limit=limit, skip=skip)

@router.post("/")
async def create_new_user(
    user: UserIn,
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session)):
    c_user = await users.get_user_by_email(session, user.email)
    token = create_access_token({"sub": user.email})
    if not c_user:
        new_user = await users.add_user(session=session, email=user.email, password=user.password, update_token=token)
        if not new_user:
            raise ACCESS_EXC
    else:
        if c_user.email_confirm == True:
            raise EMAIL_EXC
        if not verify_password(user.password, c_user.hash_password):
            raise PASS_EXC
        print(c_user.update_token)
        await users.change_token(session, int(c_user.id), token)
    text = f'To confirm email, follow the link: {MAIN_URL}/users/registration/{user.email}/{user.password}/{token}'
    confirm_email(to=user.email, text=text)

@router.get("/registration/{email}/{password}/{token}", response_model=User, response_model_exclude=["hash_password", "update_token"])
async def confirm_user_email(
    email: str,
    password : str,
    token: str,
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session)):
    n_email = get_user_email(token)
    if n_email == email:
        c_user = await users.get_user_by_email(session, email)
        if c_user.update_token != token:
            raise TOKEN_EXC
        #Пароль можно не проверять
        if not verify_password(password, c_user.hash_password):
            raise PASS_EXC
        token = create_access_token({"sub": email})
        new_user = await users.confirm_email(session=session, id=int(c_user.id), update_token=token)
        if new_user:
            user_folder = f"tracks/user_{new_user.id}"
            if not os.path.isdir(user_folder):
                os.mkdir(user_folder)
            return new_user

@router.patch("/", response_model=User, response_model_exclude=["hash_password", "update_token"])
async def update_user(
    user: UserChange,
    users: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    if not verify_password(user.password, current_user.hash_password):
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
    else:
        raise AUTH_EXC


@router.get("/recovery/{email}/{token}")
async def recover_pass(
    email: str,
    token: str,
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session)):
    user : User = await get_current_user(users, session, token)
    if user.email == email:
        new_password = secrets.token_urlsafe(10)
        new_password = new_password[:9]
        await users.update_user(session, int(user.id), user.email, hashlib.sha256(new_password.encode('utf-8')).hexdigest())
        #await users.update_user(session, int(user.id), user.email, new_password)
        text = f'New password: {new_password}'
        password_recovery(to=email, text=text)
    else:
        raise TOKEN_EXC

# @router.delete("/")

# async def delete_current_user(
    
#     user_id:int,
#     users : UserRepository = Depends(get_user_repository),
#     session : AsyncSession = Depends(get_session)
#     ):
#     user = await users.get_user_by_id(session=session, id=user_id)
#     if user.id is None:
#         raise ACCESS_EXC
#     user = await users.delete_user(session=session, id=user_id)
#     if user:
#         user_folder = f"tracks/user_{user_id}"
#         if os.path.isdir(user_folder):
#             shutil.rmtree(user_folder, ignore_errors=False, onerror=None)
#     return user