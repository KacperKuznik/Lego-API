from typing import Union
from models import *
from utils import hash_password, verify_password
from cosmosdb import database
from fastapi import FastAPI, HTTPException
import uuid
from azure.cosmos import exceptions

app = FastAPI()
users_container = database.get_container_client("users")
legosets_container = database.get_container_client("legosets")
comments_container = database.get_container_client("comments")
auctions_container = database.get_container_client("auctions")

# User
@app.post("/rest/user")
def create_user(user: UserCreate):    
    user_id = uuid.uuid4()
    hashed_password = hash_password(user.password)
    user.password = hashed_password
    new_user = {
        "id": str(user_id),
        "pk": "USER",
        "photo_url": "", #TODO
        "owned_sets": [],
        "created_at": datetime.datetime.now().isoformat(),
        **user.dict()
    }

    users_container.create_item(new_user)
    return new_user

@app.get("/rest/user")
def list_users():
    query = "SELECT * FROM c"
    users = list(users_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    users = [UserOutput(**user) for user in users]
    return users

@app.get("/rest/user/{id}")
def get_user(id: str):
    try:
        user = users_container.read_item(item=id, partition_key="USER")
        return UserOutput(**user)
    except exceptions.CosmosResourceNotFoundError:
        return {"error": "User not found"}
    
@app.put("/rest/user/{id}")
def update_user(id: str, updated_user: UserUpdate):
    try:
        user = users_container.read_item(item=id, partition_key="USER")
        
        updated_data = updated_user.dict(exclude_unset=True)
        user.update(updated_data)
        
        users_container.replace_item(item=id, body=user)
        return user
    except exceptions.CosmosResourceNotFoundError:
        return {"error": "User not found"}
    
@app.delete("/rest/user/{id}")
def delete_user(id: str):
    try:
        users_container.delete_item(item=id, partition_key="USER")
        return {"status": "User deleted successfully"}
    except exceptions.CosmosResourceNotFoundError:
        return {"error": "User not found"}
    
# # Media
# @app.post("/rest/media")
# def upload_media(): ...
# @app.get("/rest/media/{blob_name}")
# def download_media(blob_name: str): 
#     pass

# LegoSet
@app.post("/rest/legoset")
def create_legoset(lego_set: LegoSetCreate): 
    lego_set_id = uuid.uuid4()
    new_lego_set = {
        "id": str(lego_set_id),
        "name": lego_set.name,
        "pk": "LEGOSET",
        "code_number": lego_set.code_number,
        "description": lego_set.description,
        "photo_blob_names": lego_set.photo_blob_names,
        "owner_id": lego_set.owner_id,
    }
    legosets_container.create_item(new_lego_set)
    return new_lego_set


@app.get("/rest/legoset")
def list_legosets():
    query = "SELECT * FROM c"
    legosets = list(legosets_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    legosets = [LegoSetOutput(**legoset) for legoset in legosets]
    return legosets


@app.get("/rest/legoset/{id}")
def get_legoset(id: str):
    try:
        legoset = legosets_container.read_item(item=id, partition_key="LEGOSET")
        return LegoSetOutput(**legoset)
    except exceptions.CosmosResourceNotFoundError:
        return {"error": "Lego set not found"}

# @app.put("/rest/legoset/{id}")
# def update_legoset(id: str): ...
@app.delete("/rest/legoset/{id}")
def delete_legoset(id: str):
    try:
        legosets_container.delete_item(item=id, partition_key="LEGOSET")
        return {"status": "Lego set deleted successfully"}
    except exceptions.CosmosResourceNotFoundError:
        return {"error": "Lego set not found"}


# Comments
@app.post("/rest/legoset/{id}/comment")
def create_comment(id: str, comment: CommentCreate):
    # check if legoset exists
    try:
        legoset = legosets_container.read_item(item=id, partition_key="LEGOSET")
    except:
        raise HTTPException(status_code=404, detail="Lego set not found")
    #check if user exists
    try: # ?????
        user = users_container.read_item(item=comment.user_id, partition_key="USER")
    except:
        raise HTTPException(status_code=404, detail="User not found")
    # create the comment
    comment_id = uuid.uuid4()
    new_comment = {
        "id": str(comment_id),
        "pk": comment.legoset_id, # the comments get saved closer to the legoset
        "user_id": comment.user_id, # ?????
        "legoset_id": comment.legoset_id,
        "text": comment.text,
        "created_at": datetime.datetime.now().isoformat(),
    }
    comments_container.create_item(new_comment)
    return new_comment

@app.get("/rest/legoset/{id}/comment")
def list_comments(id: str): 
    try:
        legoset = legosets_container.read_item(item=id, partition_key="LEGOSET")
    except:
        raise HTTPException(status_code=404, detail="Lego set not found")

    query = f"SELECT * FROM c WHERE c.legoset_id='{id}'" 
    comments = list(comments_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    comments = [CommentOut(**comment) for comment in comments]
    return comments

# Auction
@app.post("/rest/auction")
def create_auction(auction: AuctionCreate):
    # check if legoset exists
    try:
        legoset = legosets_container.read_item(item=auction.legoset_id, partition_key="LEGOSET")
    except:
        raise HTTPException(status_code=404, detail="Lego set not found")
    #check if user exists
    try: # ?????
        user = users_container.read_item(item=auction.seller_id, partition_key="USER")
    except:
        raise HTTPException(status_code=404, detail="User not found")
    
    auction_id = uuid.uuid4()
    new_auction = {
        "id": str(auction_id),
        "pk": auction.legoset_id,
        "legoset_id": auction.legoset_id,
        "seller_id": auction.seller_id,
        "base_price": float(auction.base_price),
        "close_date": auction.close_date.isoformat(),
    } 
    auctions_container.create_item(new_auction)
    return new_auction

@app.get("/rest/auction")
def list_auctions(): 
    query = "SELECT * FROM c"
    auctions = list(auctions_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    auctions = [AuctionOut(**auction) for auction in auctions]
    return auctions

# Bid
# @app.post("/rest/auction/{id}/bid")
# def bid_auction(id: str): ...