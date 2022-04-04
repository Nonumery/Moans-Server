import json
from fastapi import APIRouter, Depends
from models.users import User
from .depends import get_current_user

router = APIRouter()

assetlinks = ""
@router.get("/assetlinks", response_model=list)
def get_assetlinks(current_user : User = Depends(get_current_user)):
    with open("./.well-known/assetlinks.json", "rb") as assets:
        if (assets != None):
            assetlinks = json.load(assets)
            return assetlinks
    