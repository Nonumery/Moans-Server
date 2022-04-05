import os
from core.config import CLIENT_ID, OATH_GOOGLE_URL
from core.errors import AUTH_EXC, CONFIRM_EXC
from endpoints.depends import get_session, get_user_repository
from models.token import Token, Login
from fastapi import APIRouter, Depends, Request
from repositories.users import UserRepository
from core.security import verify_password, create_access_token
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
    
@router.post("/google")
async def auth_user(
    request: Request,
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session)):
    f = json.loads((await request.body()).decode('utf-8'))
    email = None
    password = f['id_token']
    async with httpx.AsyncClient() as client:
        response = await client.get(OATH_GOOGLE_URL+str(password))
        response = response.json()
        if (response['azp'] == CLIENT_ID):
            email = response['email']
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