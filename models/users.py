from datetime import datetime
import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, validator, constr

class User(BaseModel):
    id : Optional[str] = None
    email: EmailStr
    hash_password: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
class UserIn(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    password2: str
    
    @validator("password2")
    def password_match(cls, v, values, **kwargs):
        if "password" in values and v!= values["password"]:
            raise ValueError("Passwords don't match")
        return v
    
class UserChange(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    new_password: constr(min_length=8)