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
    owner_id: Optional[str] = None

class LegoSetUpdate(BaseModel):
    name: Optional[str] = None
    code_number: Optional[str] = None
    description: Optional[str] = None
    photo_blob_names: Optional[List[str]] = None
    owner_id: Optional[str] = None


class LegoSetOutput(BaseModel):
    id: str
    name: str
    code_number: str
    description: Optional[str] = None
    photo_blob_names: List[str]
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
    status: str="open"


class AuctionOut(BaseModel):
    id: str
    legoset_id: str
    seller_id: str
    base_price: float
    close_date: str
    # bids: Optional[List[str]] = [] # list of bid id's
    status: str  # Add status
    winner_id: Optional[str] = None
    winning_bid: Optional[float] = None
    closed_at: Optional[str] = None
    created_at: Optional[str] = None

class BidCreate(BaseModel):
    auction_id: str
    bidder_id: str
    amount: float   


class BidOut(BaseModel):
    id: str
    auction_id: str
    bidder_id: str
    amount: float
    created_at: Optional[str] = None