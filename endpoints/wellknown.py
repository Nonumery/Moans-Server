import json
from fastapi import APIRouter, Depends
from models.users import User
from .depends import get_current_user

router = APIRouter()

assetlinks = ""
@router.get("/assetlinks.json", response_model=list)
def get_assetlinks():
    with open("./.well-known/assetlinks.json", "rb") as assets:
        if (assets != None):
            assetlinks = json.load(assets)
            return assetlinks
    