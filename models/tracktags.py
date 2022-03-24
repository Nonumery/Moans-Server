from typing import Optional
import datetime
from pydantic import BaseModel


class TrackTag(BaseModel):
    track_id : int
    tag_id : int