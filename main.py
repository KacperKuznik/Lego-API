import json
from typing import Union
from models import *
from utils import hash_password, verify_password
from cosmosdb import database
from rediscache import redis_client as r
from fastapi import FastAPI, HTTPException
import uuid
from azure.cosmos import exceptions

app = FastAPI()
users_container =    database.get_container_client("users")
legosets_container = database.get_container_client("legosets")
comments_container = database.get_container_client("comments")
auctions_container = database.get_container_client("auctions")
bids_container =     database.get_container_client("bids")



# Default deleted user
@app.on_event("startup")
def ensure_deleted_user_exists():
    deleted_user_id = "deleted-user"
    try:
        users_container.read_item(item=deleted_user_id, partition_key="USER")
    except exceptions.CosmosResourceNotFoundError:
        users_container.create_item({
            "id": deleted_user_id,
            "pk": "USER",
            "nickname": "Deleted User",
            "name": "Deleted User",
            "photo_url": "",
            "owned_sets": [],
            "password": "",
            "created_at": datetime.datetime.now().isoformat(),
        })
        print("Created default 'Deleted User'")


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
    cached_users = r.get("users_list")
    if cached_users:
        return json.loads(cached_users)
    query = "SELECT * FROM c"
    users = list(users_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    users = [UserOutput(**user) for user in users]
    r.setex("users_list", 60, json.dumps([user.model_dump() for user in users]))
    return users

@app.get("/rest/user/{id}")
def get_user(id: str):
    try:
        user = users_container.read_item(item=id, partition_key="USER")
        return UserOutput(**user)
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    
@app.put("/rest/user/{id}")
def update_user(id: str, updated_user: UserUpdate):
    try:
        user = users_container.read_item(item=id, partition_key="USER")
        
        updated_data = updated_user.dict(exclude_unset=True)
        user.update(updated_data)
        
        users_container.replace_item(item=id, body=user)
        return user
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    
@app.delete("/rest/user/{id}")
def delete_user(id: str):
    try:
        users_container.read_item(item=id, partition_key="USER")

        # Update all comments made by deleted user
        comment_query = f"SELECT * FROM c WHERE c.user_id = '{id}'"
        comments = list(comments_container.query_items(
            query=comment_query, enable_cross_partition_query=True
        ))
        for comment in comments:
            comment["user_id"] = "deleted-user"
            comments_container.replace_item(item=comment["id"], body=comment)

        # Update all auctions
        auction_query = f"SELECT * FROM c WHERE c.seller_id = '{id}'"
        auctions = list(auctions_container.query_items(
            query=auction_query, enable_cross_partition_query=True
        ))
        for auction in auctions:
            auction["seller_id"] = "deleted-user"
            auctions_container.replace_item(item=auction["id"], body=auction)

        # Update all bids
        bid_query = f"SELECT * FROM c WHERE c.bidder_id = '{id}'"
        bids = list(bids_container.query_items(
            query=bid_query, enable_cross_partition_query=True
        ))
        for bid in bids:
            bid["bidder_id"] = "deleted-user"
            bids_container.replace_item(item=bid["id"], body=bid)

        # Delete the user
        users_container.delete_item(item=id, partition_key="USER")

        return {"status": f"User {id} deleted successfully"}

    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    
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
        "created_at": datetime.datetime.now().isoformat(),
        "owner_id": lego_set.owner_id,
    }
    legosets_container.create_item(new_lego_set)
    return new_lego_set


@app.get("/rest/legoset")
def list_legosets():
    cached_legoset = r.get("legosets_list")
    if cached_legoset:
        return json.loads(cached_legoset)
    query = "SELECT * FROM c"
    legosets = list(legosets_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    legosets = [LegoSetOutput(**legoset) for legoset in legosets]
    r.setex("legosets_list", 60, json.dumps([legoset.model_dump() for legoset in legosets]))
    return legosets


@app.get("/rest/legoset/{id}")
def get_legoset(id: str):
    try:
        legoset = legosets_container.read_item(item=id, partition_key="LEGOSET")
        return LegoSetOutput(**legoset)
    except exceptions.CosmosResourceNotFoundError:
        return {"error": "Lego set not found"}

@app.put("/rest/legoset/{id}")
def update_legoset(id: str, updated_legoset: LegoSetUpdate):
    try:
        legoset = legosets_container.read_item(item=id, partition_key="LEGOSET")
        updated_data = updated_legoset.dict(exclude_unset=True)
        legoset.update(updated_data)
        legosets_container.replace_item(item=id, body=legoset)
        return legoset
    except exceptions.CosmosResourceNotFoundError:
        return {"error": "Lego set not found"}        

@app.delete("/rest/legoset/{id}")
def delete_legoset(id: str):
    try:
        legosets_container.delete_item(item=id, partition_key="LEGOSET")
        return {"status": "Lego set deleted successfully"}
    except exceptions.CosmosResourceNotFoundError:
        return {"error": "Lego set not found"}

# List of LegoSets of a given user
@app.get("/rest/user/{user_id}/legosets")
def list_legosets_of_user(user_id: str):
    query = f"SELECT * FROM c WHERE c.owner_id = '{user_id}'"
    legosets = list(legosets_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    if not legosets:
        raise HTTPException(status_code=404, detail="No Lego sets found for this user")
    legosets = [LegoSetOutput(**legoset) for legoset in legosets]
    return legosets

# List of most recently added LegoSets
@app.get("/rest/legoset/recent")
def list_recent_legosets(limit: int = 10):
    query = f"SELECT * FROM c ORDER BY c.created_at DESC OFFSET 0 LIMIT {limit}"
    legosets = list(legosets_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    if not legosets:
        raise HTTPException(status_code=404, detail="No Lego sets found")
    legosets = [LegoSetOutput(**legoset) for legoset in legosets]
    return legosets


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
    # check if user exists
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
        "status": "open",  # Add initial status
        "created_at": datetime.datetime.now().isoformat()
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

# Search Auctions for a given LegoSet
@app.get("/rest/auction/search")
def search_auctions_by_legoset(legoset_id: str):
    query = f"SELECT * FROM c WHERE c.legoset_id = '{legoset_id}'"
    auctions = list(auctions_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    if not auctions:
        raise HTTPException(status_code=404, detail="No auctions found for this Lego set")
    auctions = [AuctionOut(**auction) for auction in auctions]
    return auctions

# Bid
@app.post("/rest/auction/{id}/bid")
def bid_auction(id: str, bid: BidCreate):
    # check if auction exists
    query = f"SELECT * FROM c WHERE c.id = '{id}'"
    results = list(auctions_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

    if not results:
        raise HTTPException(status_code=404, detail="Auction not found")

    #check if user exists
    try: # ?????
        user = users_container.read_item(item=bid.bidder_id, partition_key="USER")
    except:
        raise HTTPException(status_code=404, detail="User not found")

    auction = results[0]

    # get bids to check the highest amount
    query = f"SELECT * FROM c WHERE c.auction_id='{id}' ORDER BY c.amount DESC" 
    bids = list(bids_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

    if bids:
        highest_bid = bids[0]["amount"]
        # refuse request if the bid is too small
        if float(bid.amount) <= float(highest_bid):
            raise HTTPException(status_code=403, detail="Bid amount is too small")
    if float(auction["base_price"]) > float(bid.amount):
        raise HTTPException(status_code=403, detail="Bid amount is smaller than base price")

    bid_id = uuid.uuid4()
    new_bid = {
        "id": str(bid_id),
        "auction_id": auction["id"],
        "bidder_id": bid.bidder_id,
        "amount": float(bid.amount)
    }
    bids_container.create_item(new_bid)
    return new_bid

