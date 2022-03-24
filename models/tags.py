from typing import Optional
import datetime
from pydantic import BaseModel


class TagIn(BaseModel):
    tag : str

class Tag(TagIn):
    id : Optional[int] = None
    

