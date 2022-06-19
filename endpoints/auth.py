import os
from core.config import CLIENT_ID, OATH_GOOGLE_URL
from core.errors import AUTH_EXC, CONFIRM_EXC, CRED_EXC
from endpoints.depends import get_session, get_user_email, get_user_repository
from models.token import Token, Login, Tokens
from fastapi import APIRouter, Depends, Request
from repositories.users import UserRepository
from core.security import create_refresh_token, verify_password, create_access_token
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import json

router = APIRouter()


@router.post("/", response_model=Token)
async def login(
        login: Login,
        users: UserRepository = Depends(get_user_repository),
        session: AsyncSession = Depends(get_session)):
    user = await users.get_user_by_email(session, login.email)
    if user is None or not verify_password(login.password, user.hash_password):
        raise AUTH_EXC
    if user.email_confirm == False:
        raise CONFIRM_EXC
    return Token(
        access_token=create_access_token({"sub": user.email}),
        token_type="Bearer"
    )


@router.post("/new_login", response_model=Tokens)
async def new_login(
        request: Request,
        login: Login,
        users: UserRepository = Depends(get_user_repository),
        session: AsyncSession = Depends(get_session)):
    user = await users.get_user_by_email(session, login.email)
    if user is None or not verify_password(login.password, user.hash_password):
        raise AUTH_EXC
    if user.email_confirm == False:
        raise CONFIRM_EXC

    s = await users.get_new_session(session, user,
                                    create_refresh_token({"sub": user.email}),
                                    request.headers)
    if s:
        return Tokens(
            access_token=create_access_token({"sub": user.email}),
            refresh_token=s.refresh_token,
            token_type="Bearer"
        )


@router.post("/logout")
async def logout(
        request: Request,
        refresh_token: str,
        users: UserRepository = Depends(get_user_repository),
        session: AsyncSession = Depends(get_session)):
    email = get_user_email(refresh_token)
    user = await users.get_user_by_email(session, email)
    if user.email_confirm == False:
        raise CONFIRM_EXC

    s = await users.delete_session(session, user,
                                   refresh_token,
                                   request.headers)
    return s


@router.post("/refresh", response_model=Tokens)
async def refresh_token(
        request: Request,
        refresh_token: str,
        users: UserRepository = Depends(get_user_repository),
        session: AsyncSession = Depends(get_session)):

    email = get_user_email(refresh_token)
    user = await users.get_user_by_email(session, email)
    if not user:
        raise CRED_EXC
    if user.email_confirm == False:
        raise CONFIRM_EXC

    s = await users.get_new_session(session, user,
                                    refresh_token,
                                    request.headers)
    if s:
        return Tokens(
            access_token=create_access_token({"sub": user.email}),
            refresh_token=s.refresh_token,
            token_type="Bearer"
        )


async def delete_track(self, session: AsyncSession, refresh: str):
    try:
        refresh = await self.get_track_by_refresh(session, id)
        await session.delete(refresh)
        return True
    except Exception as e:
        print("delete_track", type(e))
        return False


async def _get_email(id_token: str) -> str | None:
    async with httpx.AsyncClient() as client:
        response = await client.get(f'{OATH_GOOGLE_URL}{id_token}')
        response = response.json()
        if (response['azp'] == CLIENT_ID):
            return response['email']


@router.post("/google")
async def auth_user(
        request: Request,
        users: UserRepository = Depends(get_user_repository),
        session: AsyncSession = Depends(get_session)):
    info = json.loads((await request.body()).decode('utf-8'))
    email = None
    password = info['id_token']
    email = await _get_email(str(password))
    if email:
        token = create_access_token({"sub": email})
        c_user = await users.get_user_by_email(session, email)
        if not c_user:
            c_user = await users.add_user(session=session, email=email, password=password, update_token=token, email_confirm=True)
            if c_user:
                user_folder = f"tracks/user_{c_user.id}"
                if not os.path.isdir(user_folder):
                    os.mkdir(user_folder)
        return Token(
            access_token=token,
            token_type="Bearer"
        )
