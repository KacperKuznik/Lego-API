from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import datetime

class UserCreate(BaseModel):
    nickname: str = Field(..., min_length=3)
    name: str
    password: str


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    name: Optional[str] = None
    photo_url: Optional[str] = None


class UserOutput(BaseModel):
    id: str
    nickname: str
    name: str
    photo_url: str
    owned_sets: List[str]


class MediaOutput(BaseModel):
    blob_name: str
    url: str


class LegoSetCreate(BaseModel):
    name: str
    code_number: str
    description: Optional[str] = None
    photo_blob_names: List[str] = Field(..., min_items=1)


class LegoSetUpdate(BaseModel):
    name: Optional[str] = None
    code_number: Optional[str] = None
    description: Optional[str] = None
    photo_blob_names: Optional[List[str]] = None


class LegoSetOutput(BaseModel):
    id: str
    name: str
    code_number: str
    description: Optional[str] = None
    photo_urls: List[str]
    owner_id: Optional[str] = None


class CommentCreate(BaseModel):
    user_id: str
    text: str
    legoset_id: str


class CommentOut(BaseModel):
    id: str
    legoset_id: str
    user_id: str
    text: str
    created_at: str


class AuctionCreate(BaseModel):
    legoset_id: str
    seller_id: str
    base_price: float
    close_date: datetime.datetime


class AuctionOut(BaseModel):
    id: str
    legoset_id: str
    seller_id: str
    base_price: float
    close_date: str
    bids: List[dict]


class BidCreate(BaseModel):
    bidder_id: str
    amount: float