from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Union
from typing import Optional

class UserIn(BaseModel):
    email: str

class UserWithPassword(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    description: Optional[str] = None