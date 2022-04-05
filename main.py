import asyncio
import json
import os
import shutil
from fastapi import Depends, FastAPI, Request, Response, staticfiles, status
from fastapi.responses import RedirectResponse, HTMLResponse
from httpcore import URL
from pytest import Session
import uvicorn
from core.config import INSTALL_APP
from db.tables import Base, engine, LanguageTable
from endpoints import users, auth, tracks, wellknown
from sqlalchemy import insert
import asyncio
import typer
from endpoints.depends import get_session, get_track_repository

from repositories.tracks import TrackRepository

async def init_models():
    async with engine.begin() as conn:
        #await conn.run_sync(Base.metadata.drop_all)
        #if (os.path.isdir("tracks")):
            #shutil.rmtree("tracks", ignore_errors=False, onerror=None)
        await conn.run_sync(Base.metadata.create_all)
        if not (os.path.isdir("tracks")):
            os.mkdir("tracks")
        try:
            await conn.execute(insert(LanguageTable).values(id = 0, language="rus"))
            await conn.execute(insert(LanguageTable).values(id = 1, language="eng"))
        except(Exception):
            print("Already exists")

app = FastAPI(title="Moans Server")
app.include_router(router=users.router, prefix="/users", tags=["users"])
app.include_router(router=auth.router, prefix="/auth", tags=["auth"])
app.include_router(router=tracks.router, prefix="/tracks", tags=["tracks"])
#app.include_router(router=wellknown.router, prefix="/.well-known", tags=["well-known"])
@app.get("/")
def main():
    return {"status": "ok"}
# app.mount("/tracks_", staticfiles.StaticFiles(directory="tracks"), name="tracks")

# @app.get("/audios")

# async def get_tracks(
    
#     user_id: int
# ):
#     out = []
#     for filename in os.listdir(f"tracks/user_{user_id}"):
#         out.append({
#             "name": filename.split(".")[0],
#             "path": f"/tracks_/user_{user_id}/" + filename
#         })
#     return out

cli = typer.Typer()

@cli.command()
def db_init_models():
    asyncio.run(init_models())
    print("Done")
    uvicorn.run("main:app", port = 8000, host="127.0.0.1", reload=True)



if __name__ == "__main__":
    asyncio.run(cli())
    