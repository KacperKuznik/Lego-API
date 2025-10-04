from typing import Union
from models import *
from utils import hash_password, verify_password
from cosmosdb import database
from fastapi import FastAPI
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
# def download_media(blob_name: str): ...

# # LegoSet
# @app.post("/rest/legoset")
# def create_legoset(): ...
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

# # Comments
# @app.post("/rest/legoset/{id}/comment")
# def create_comment(id: str): ...
# @app.get("/rest/legoset/{id}/comment")
# def list_comments(id: str): ...

# # Auction
# @app.post("/rest/auction")
# def create_auction(): ...
# @app.get("/rest/auction")
# def list_auctions(): ...
# @app.post("/rest/auction/{id}/bid")
# def bid_auction(id: str): ...