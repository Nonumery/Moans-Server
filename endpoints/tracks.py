from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import Response
from core.config import AUDIO_FORMAT, ERROR_DETAIL, MEDIA_FORMAT
from db.tables import Status, Voice
from models.trackchecked import TrackChecked
from models.users import User
from repositories.tracks import TrackRepository
from .depends import get_current_user, get_session, get_track_repository, get_user_repository
from models.tracks import Language, Track, TrackIn, TrackInfo, UserTrack
from sqlalchemy.ext.asyncio import AsyncSession
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
    if not await tracks.get_language(session, language_id):   
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="Language doesn't exist")
    if await tracks.get_track(session, int(current_user.id), name):
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="Track name isn't avaluable")
    tr = TrackIn(name=name, description=description, voice=voice, language_id=language_id)
    try:
        print(1)
        tr = TrackIn(name=name, description=description, voice=voice, language_id=language_id)
        print(1)
        path=""
        print(1)
        user_folder = f"tracks/user_{current_user.id}"
        print(1)
        tr_name = datetime.now()
        if not os.path.isdir(user_folder):
            os.mkdir(user_folder)
        with open(f'{user_folder}/{tr_name}.mp3', "wb") as buffer:
            shutil.copyfileobj(record.file, buffer)
            path = f'{user_folder}/{tr_name}.mp3'
    except(Exception):
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=ERROR_DETAIL)
    track = await tracks.create_new_track(session=session, user_id = int(current_user.id), path=path, tr=tr, tags_string=tag)
    if track is None:
        os.remove(path)
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=ERROR_DETAIL)
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
    track = await tracks.get_track_by_id(session, id)
    if track is None or track.user_id != int(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")
    if not await tracks.get_language(session, language_id):   
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="Language doesn't exist")
    old_track = await tracks.get_track(session, int(current_user.id), name)
    if old_track is not None and old_track.id != id: 
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="Track name isn't avaluable")
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
    try:
        tracks = await tracks.get_track_feed(session=session, user_id=int(current_user.id), language_id=language_id, voice=voice, limit=limit, skip=skip)
        return tracks
    except(Exception):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")

@router.get("/refresh")
async def refresh_track_list(
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    try:
        tracks = await tracks.checks_to_views(session=session, user_id=int(current_user.id))
        return tracks
    except(Exception):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")

@router.get("/track/", response_model=TrackInfo, response_model_exclude=["path", "status", "likes"])
async def get_track_info(
    track_id: int,
    tracks : TrackRepository = Depends(get_track_repository),
    current_user : User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)):
    track = await tracks.get_user_track_by_id(session=session, user_id=int(current_user.id), track_id=track_id)
    if track is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")
    return track


@router.get("/my_tracks", response_model=List[UserTrack])
async def get_user_tracks(
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session),
    limit : int = 10,
    skip: int = 0):
    
    return await tracks.get_user_tracks(session=session, user_id=int(current_user.id), limit=limit, skip=skip)


@router.get("/seen", response_model=List[TrackInfo], response_model_exclude=["path", "status", "voice", "language_id"])
async def get_checked_tracks(
    language_id : int,
    voice : Voice,
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session),
    limit : int = 10,
    skip: int = 0):
    return await tracks.get_track_seen(session=session, user_id=int(current_user.id), language_id=language_id, voice=voice, limit=limit, skip=skip)

@router.get("/liked", response_model=List[TrackInfo], response_model_exclude=["path", "status", "voice", "language_id"])
async def get_liked_tracks(
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session),
    limit : int = 10,
    skip: int = 0):
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
    print(track.json())
    headers = { "track":track.json(), }
    with open(track.path, "rb") as audio:
        data = audio.read()
    return Response(data, headers=headers, media_type=MEDIA_FORMAT)


@router.get("/get_audio")
async def get_track_audio(
    track_id : int,
    tracks : TrackRepository = Depends(get_track_repository),
    session : AsyncSession = Depends(get_session)
    ):
    track = await tracks.get_track_by_id(session, track_id)
    if track is None: 
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="Track name isn't avaluable")
    with open(track.path, "rb") as audio:
        data = audio.read()
    return Response(data, media_type=MEDIA_FORMAT)#StreamingResponse
    
@router.get("/get_audio_bytes")
async def get_track_audio_bytes(
    track_id : int,
    start : int,
    end : int,
    tracks : TrackRepository = Depends(get_track_repository),
    session : AsyncSession = Depends(get_session)
    ):
    track = await tracks.get_track_by_id(session, track_id)
    with open(track.path, "rb") as audio:
        filesize = str(os.stat(track.path).st_size)
        if start >= end or start < 0 or end < 0 or start > int(filesize) or end > int(filesize):
            start = 0
            end = 0
        audio.seek(start)
        data = audio.read(end - start)
        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{filesize}',
            'Accept-Ranges': 'bytes'
        }
    return Response(data, status_code=206, headers=headers, media_type=MEDIA_FORMAT)


@router.delete("/")
async def delete_current_track(
    track_id:int,
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    track = await tracks.get_track_by_id(session=session, id=id)
    if track.user_id is None or track.user_id != int(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")
    os.remove(track.path)
    return await tracks.delete_track(session=session, id=track_id)


@router.post("/check")
async def check_track(
    track_id: int,
    tracks: TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    result = await tracks.check_track(session=session, track_id=track_id, user_id=int(current_user.id))
    if not result:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")
    return result

@router.patch("/set_track_status", response_model=TrackInfo, response_model_exclude=["path", "status", "voice", "language_id"])
async def set_status(
    track_id: int = Form(...),
    track_status : Status = Form(...),
    tracks: TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    track = await tracks.get_track_by_id(session, track_id)
    if track is None or track.user_id != int(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")
    if (int(track_status.value) > int(Status.publish) or int(track.__dict__["status"]) > int(Status.publish)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")
    return await tracks.update_status(session=session, id=track_id, status=track_status)

@router.patch("/like")
async def like_track(
    track_id: int,
    liked: bool,
    tracks : TrackRepository = Depends(get_track_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
    ):
    result = await tracks.like_track(session=session, track_id=track_id, user_id=int(current_user.id), liked=liked)
    print(result)
    if not result:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")
    return result

@router.get("/get_logo")
async def get_app_logo():
    with open("resources/logo.png", "rb") as logo:
        data = logo.read()
    return Response(data, media_type="image/png")
