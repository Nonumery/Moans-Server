from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Request, status, UploadFile, File, Form
from fastapi.responses import Response, HTMLResponse
from httpx import URL
from core.config import AUDIO_FORMAT, MEDIA_FORMAT, IMAGE_FORMAT
from core.errors import ACCESS_EXC, CONFIRM_EXC, INPUT_EXC, LANG_EXC, NAME_EXC, RECORD_EXC
from core.send import get_html
from db.tables import Status, Voice
from models.users import User
from repositories.tracks import TrackRepository
from .depends import get_current_user, get_session, get_track_repository, get_user_repository
from models.tracks import Language, TrackIn, TrackInfo, UserTrack
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exc
import shutil
import os

router = APIRouter()

@router.get("/getLanguages", response_model=List[Language])
async def all_languages(tracks : TrackRepository = Depends(get_track_repository), session : AsyncSession = Depends(get_session)):
    return await tracks.all_langs(session)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TrackInfo, response_model_exclude=["path", "status", "voice", "language_id"])
async def add_new_track(
    name : str = Form(...),
    description : str = Form(...),
    voice : Voice = Form(...),
    language_id : int = Form(...),
    tag: str = Form(...),
    record : UploadFile = File(...),
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    if not await tracks.get_language(session, language_id):   
        raise LANG_EXC
    if await tracks.get_track(session, int(current_user.id), name):
        raise NAME_EXC
    tr = TrackIn(name=name, description=description, voice=voice, language_id=language_id)
    try:
        tr = TrackIn(name=name, description=description, voice=voice, language_id=language_id)
        path=""
        user_folder = f"tracks/user_{current_user.id}"
        tr_name = datetime.now()
        if not os.path.isdir(user_folder):
            os.mkdir(user_folder)
        with open(f'{user_folder}/{tr_name}.{AUDIO_FORMAT}', "wb") as buffer:
            shutil.copyfileobj(record.file, buffer)
            path = f'{user_folder}/{tr_name}.{AUDIO_FORMAT}'
    except Exception as e:
        print("add_new_track", type(e))
        raise RECORD_EXC
    track = await tracks.create_new_track(session=session, user_id = int(current_user.id), path=path, tr=tr, tags_string=tag)
    if track is None:
        os.remove(path)
        raise RECORD_EXC
    return track


@router.post("/update", response_model=TrackInfo, response_model_exclude=["path", "status", "voice", "language_id"])
async def update_current_track(
    id: int = Form(...),
    name : str = Form(...),
    description : str = Form(...),
    voice : Voice = Form(...),
    language_id : int = Form(...),
    tags: str = Form(...),
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    track = await tracks.get_track_by_id(session, id)
    if track is None or track.user_id != int(current_user.id):
        raise ACCESS_EXC
    if not await tracks.get_language(session, language_id):   
        raise LANG_EXC
    old_track = await tracks.get_track(session, int(current_user.id), name)
    if old_track is not None and old_track.id != id: 
        raise NAME_EXC
    tr = TrackIn(
        name=name,
        description=description,
        voice=voice,
        language_id=language_id
    )

    return await tracks.update_track(session=session, id=id, tr=tr, tags_string=tags)


@router.get("/", response_model=List[TrackInfo], response_model_exclude=["path", "status", "voice", "language_id"])
async def get_unchecked_tracks(
    language_id: int,
    voice : Voice,
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session),
    limit : int = 10,
    skip: int = 0):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    try:
        tracks = await tracks.get_track_feed(session=session, user_id=int(current_user.id), language_id=language_id, voice=voice, limit=limit, skip=skip)
        return tracks
    except exc.DBAPIError as e:
        #ошибка из-за некорректного ввода limit и skip
        raise ACCESS_EXC    
    except Exception as e:
        print("get_unchecked_tracks", type(e))
        raise ACCESS_EXC

@router.get("/refresh")
async def refresh_track_list(
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    try:
        tracks = await tracks.checks_to_views(session=session, user_id=int(current_user.id))
        return tracks
    except Exception as e:
        print("refresh_track_list", type(e))
        raise ACCESS_EXC

@router.get("/track/", response_model=TrackInfo, response_model_exclude=["path", "likes"])
async def get_my_track_info(
    track_id: int,
    tracks : TrackRepository = Depends(get_track_repository),
    current_user : User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    track = await tracks.get_user_track_by_id(session=session, user_id=int(current_user.id), track_id=track_id)
    if track is None:
        raise ACCESS_EXC
    return track


@router.get("/my_tracks", response_model=List[UserTrack])
async def get_user_tracks(
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session),
    limit : int = 10,
    skip: int = 0):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    if limit < 0 or skip < 0:
        raise INPUT_EXC
    return await tracks.get_user_tracks(session=session, user_id=int(current_user.id), limit=limit, skip=skip)

@router.get("/track", response_model=TrackInfo, response_model_exclude=["path", "status", "voice", "language_id"])
async def get_track(
    id : int,
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    return await tracks.get_track_info_by_id(session=session, id=id)


@router.get("/seen", response_model=List[TrackInfo], response_model_exclude=["path", "status", "voice", "language_id"])
async def get_checked_tracks(
    language_id : int,
    voice : Voice,
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session),
    limit : int = 10,
    skip: int = 0):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    if limit < 0 or skip < 0:
        raise INPUT_EXC
    return await tracks.get_track_seen(session=session, user_id=int(current_user.id), language_id=language_id, voice=voice, limit=limit, skip=skip)

@router.get("/liked", response_model=List[TrackInfo], response_model_exclude=["path", "status", "voice", "language_id"])
async def get_liked_tracks(
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session),
    limit : int = 10,
    skip: int = 0):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    if limit < 0 or skip < 0:
        raise INPUT_EXC
    return await tracks.get_track_liked(session=session, user_id=int(current_user.id), limit=limit, skip=skip)

@router.get("/with_tags", response_model=List[TrackInfo], response_model_exclude=["path", "status", "voice", "language_id"])
async def get_tracks_with_tags(
    language_id: int,
    voice : Voice,
    tags : str,
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session),
    limit : int = 10,
    skip: int = 0):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    if limit < 0 or skip < 0:
        raise INPUT_EXC
    return await tracks.get_track_feed_with_tags(session=session, user_id=int(current_user.id), language_id=language_id, voice=voice, tags=tags, limit=limit, skip=skip)

@router.get("/with_audio")
async def get_track_with(
    track_id : int,
    tracks : TrackRepository = Depends(get_track_repository),
    session : AsyncSession = Depends(get_session)
    ):
    track = await tracks.get_track_by_id(session, track_id)
    if track is None:
        return {'Error':'Track is not found'}
    headers = { "track":str(track.__dict__), }
    with open(track.path, "rb") as audio:
        data = audio.read()
    return Response(data, headers=headers, media_type=MEDIA_FORMAT)


@router.get("/get_audio")
async def get_track_audio(
    track_id : int,
    range : Optional[str] = Header(None),
    tracks : TrackRepository = Depends(get_track_repository),
    session : AsyncSession = Depends(get_session)
    ):
    track = await tracks.get_track_by_id(session, track_id)
    if track is None: 
        raise ACCESS_EXC
    with open(track.path, "rb") as audio:
        filesize = str(os.stat(track.path).st_size)
        try:
            if range is None:
                start = 0
                end = int(filesize)
            else:
                s = range.split("=")[-1].split("-")
                start = int(s[0])
                if not s[1]:
                    end = int(filesize)
                else:
                    end = int(s[1])
                    if (start==end):
                        start, end = 0, 1
            audio.seek(start)
            data = audio.read(end - start+1)
            headers = {
                'Content-Range': f'bytes {str(start)}-{str(end)}/{filesize}',
                'Accept-Ranges': 'bytes'
                    }
            return Response(data, status_code=206, headers=headers, media_type=MEDIA_FORMAT)#StreamingResponse
        except ValueError as e:
            raise INPUT_EXC
        except Exception as e:
            print("get_track_audio", type(e))
            raise ACCESS_EXC

@router.delete("/")
async def delete_current_track(
    track_id:int,
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    track = await tracks.get_track_by_id(session=session, id=track_id)
    if track is None or track.user_id is None or track.user_id != int(current_user.id):
        raise ACCESS_EXC
    os.remove(track.path)
    return await tracks.delete_track(session=session, id=track_id)


@router.post("/check")
async def check_track(
    track_id: int,
    tracks: TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    if (await tracks.get_user(session, id=track_id)) == int(current_user.id):
        raise ACCESS_EXC # или владелец трека пытается чекнуть свой же трек, или такого трека не существует
    result = await tracks.check_track(session=session, track_id=track_id, user_id=int(current_user.id))
    if not result:
        raise ACCESS_EXC#TODO: Сделать исключение Track is not found
    return result

@router.patch("/set_track_status", response_model=TrackInfo, response_model_exclude=["path", "voice", "language_id"])
async def set_status(
    track_id: int = Form(...),
    track_status : Status = Form(...),
    tracks: TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    track = await tracks.get_track_by_id(session, track_id)
    if track is None or track.user_id != int(current_user.id):
        raise ACCESS_EXC#TODO: Сделать исключение Track is not found
    if (int(track_status.value) > int(Status.publish) or int(track.__dict__["status"]) > int(Status.publish)):
        raise ACCESS_EXC# запрет на переключение статуса трека на заблокированный и удаленный; нет доступа
    return await tracks.update_status(session=session, id=track_id, status=track_status)

@router.patch("/like")
async def like_track(
    track_id: int,
    liked: bool,
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    if current_user.email_confirm == False:
        raise CONFIRM_EXC
    if (await tracks.get_user(session, id=track_id)) == int(current_user.id):
        raise ACCESS_EXC # или владелец трека пытается поставить лайк, или такого трека не существует
    result = await tracks.like_track(session=session, track_id=track_id, user_id=int(current_user.id), liked=liked)
    if not result:
        raise ACCESS_EXC
    return result

@router.get("/get_logo")
async def get_app_logo():
    with open("resources/logo.png", "rb") as logo:
        data = logo.read()
    return Response(data, media_type=IMAGE_FORMAT)
    
@router.get("/track_{id}")
async def get_track_or_install(id : int, request: Request, tracks : TrackRepository = Depends(get_track_repository), session : AsyncSession = Depends(get_session)):
    d = request.headers['User-Agent']
    track = await tracks.get_track_info_by_id(session, id)
    if not track:
        raise ACCESS_EXC
    ios = "iPhone OS" in d
    content = get_html(ios, id, track.name, track.description, track.tags)
    return HTMLResponse(content=content, status_code=200)
