from typing import Optional
import datetime
from pydantic import BaseModel


class TrackChecked(BaseModel):
    track_id : int
    user_id : int
    liked : bool = False