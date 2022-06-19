from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class Login(BaseModel):
    email: EmailStr
    password: str


class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
