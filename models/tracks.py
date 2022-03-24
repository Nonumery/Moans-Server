from typing import Optional, List
import datetime
from pydantic import BaseModel

from models.tags import Tag, TagIn
from db.tables import TagTable, Voice, Status

class BaseTrack(BaseModel):
    name: str
    description: str
    voice: Voice = Voice.they_them
    status: Status = Status.publish
    language_id : int

class Track(BaseTrack):
    id : Optional[int] = None
    user_id : int
    path : str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
class TrackIn(BaseTrack):
    pass

class TrackWithTags(BaseModel):
    track: Track
    tags: Optional[List[Tag]]
    likes: Optional[int]

class UserTrack(BaseModel):
    id:int
    name: str
    status: Status = Status.publish
    likes: Optional[int]

class TrackInfo(UserTrack):
    description: str
    path: str
    tags: Optional[str]
    voice: Optional[Voice]
    language_id: Optional[int]
    liked: Optional[bool] = False
    
class TrackInfo2(UserTrack):
    description: str
    path: str
    tags: List[str]
    

class Language(BaseModel):
    id : int
    language : str