import asyncio
import os
import shutil
from fastapi import FastAPI
import uvicorn
from db.tables import Base, engine, LanguageTable
from endpoints import users, auth, tracks
from sqlalchemy import insert
import asyncio
import typer

async def init_models():
    async with engine.begin() as conn:
        #await conn.run_sync(Base.metadata.drop_all)
        if (os.path.isdir("tracks")):
            shutil.rmtree("tracks", ignore_errors=False, onerror=None)
        await conn.run_sync(Base.metadata.create_all)
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
@app.get("/")
def main():
    return {"status": "ok"}

cli = typer.Typer()

@cli.command()
def db_init_models():
    asyncio.run(init_models())
    print("Done")
    uvicorn.run("main:app", port = 8000, host="0.0.0.0", reload=True)



if __name__ == "__main__":
    asyncio.run(cli())
    