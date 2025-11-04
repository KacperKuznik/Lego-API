from faker import Faker
import uuid
import os
import random
import datetime
from cosmosdb import database
from blobstorage import BlobStorageManager
from models import UserCreate, LegoSetCreate, CommentCreate, AuctionCreate, BidCreate
import asyncio
from typing import List
import json

fake = Faker()

# Initialize containers
users_container = database.get_container_client("users")
legosets_container = database.get_container_client("legosets")
comments_container = database.get_container_client("comments")
auctions_container = database.get_container_client("auctions")
bids_container = database.get_container_client("bids")

# Initialize blob storage
blob_manager = BlobStorageManager()

# Load comment templates
COMMENT_TEMPLATES = [
    "I recently purchased the {product} and it was such a fun building experience!",
    "The {product} is amazing! It took me several hours to assemble.",
    "I was impressed by the detail and quality of the {product}.",
    "This {product} kept me entertained for hours.",
    "I love the {product}! It's the perfect mix of creativity and complexity.",
    # Add more templates as needed
]

def create_user() -> dict:
    """Create a new user with fake data"""
    first_name = fake.first_name()
    last_name = fake.last_name()
    nickname = f"{first_name}.{last_name}"
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "pk": "USER",
        "nickname": nickname,
        "name": f"{first_name} {last_name}",
        "password": fake.password(),
        "photo_url": "",  # TODO: Add user photos if needed
        "owned_sets": [],
        "created_at": datetime.datetime.now().isoformat()
    }
    
    return users_container.create_item(body=user)

def create_legoset(owner_id: str = None) -> dict:
    """Create a new lego set with fake data and images"""
    # Get random images for this lego set (1-3 images)
    image_count = random.randint(1, 3)
    base_path = os.path.join(os.path.dirname(__file__), "proj-test", "images")
    available_images = [f for f in os.listdir(base_path) if f.endswith('.jpg')]
    selected_images = random.sample(available_images, image_count)
    image_paths = [os.path.join(base_path, img) for img in selected_images]
    
    # Upload images to blob storage
    legoset_id = str(uuid.uuid4())
    blob_names = blob_manager.upload_legoset_images(image_paths, legoset_id)
    
    # Create lego set
    legoset = {
        "id": legoset_id,
        "pk": "LEGOSET",
        "name": fake.catch_phrase(),
        "code_number": f"{random.randint(1000, 9999)}-{random.randint(1, 9)}",
        "description": fake.text(max_nb_chars=200),
        "photo_blob_names": blob_names,
        "owner_id": owner_id,
        "created_at": datetime.datetime.now().isoformat()
    }
    
    return legosets_container.create_item(body=legoset)

def create_comment(user_id: str, legoset_id: str, legoset_name: str) -> dict:
    """Create a new comment for a lego set"""
    template = random.choice(COMMENT_TEMPLATES)
    comment = {
        "id": str(uuid.uuid4()),
        "pk": legoset_id,
        "user_id": user_id,
        "legoset_id": legoset_id,
        "text": template.format(product=legoset_name),
        "created_at": datetime.datetime.now().isoformat()
    }
    
    return comments_container.create_item(body=comment)

def create_auction(legoset_id: str, seller_id: str) -> dict:
    """Create a new auction for a lego set"""
    close_date = datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 30))
    auction = {
        "id": str(uuid.uuid4()),
        "pk": legoset_id,
        "legoset_id": legoset_id,
        "seller_id": seller_id,
        "base_price": round(random.uniform(10.0, 500.0), 2),
        "close_date": close_date.isoformat(),
        "status": "open",
        "created_at": datetime.datetime.now().isoformat()
    }
    
    return auctions_container.create_item(body=auction)

def create_bid(auction_id: str, bidder_id: str, current_price: float) -> dict:
    """Create a new bid for an auction"""
    bid = {
        "id": str(uuid.uuid4()),
        "pk": auction_id,
        "auction_id": auction_id,
        "bidder_id": bidder_id,
        "amount": round(current_price + random.uniform(1.0, 50.0), 2),
        "created_at": datetime.datetime.now().isoformat()
    }
    
    return bids_container.create_item(body=bid)

def populate_database():
    """Populate the database with test data"""
    print("Creating users...")
    users = [create_user() for _ in range(200)]
    print(f"Created {len(users)} users")

    print("\nCreating lego sets...")
    legosets = []
    for _ in range(500):
        # 70% chance of having an owner
        owner = random.choice(users) if random.random() < 0.7 else None
        owner_id = owner["id"] if owner else None
        legoset = create_legoset(owner_id)
        legosets.append(legoset)
        if owner:
            owner["owned_sets"].append(legoset["id"])
            users_container.replace_item(item=owner["id"], body=owner)
    print(f"Created {len(legosets)} lego sets")

    print("\nCreating comments...")
    comments_count = 0
    for legoset in legosets:
        # Create 0-5 comments per lego set
        comment_count = random.randint(0, 5)
        for _ in range(comment_count):
            comment = create_comment(
                user_id=random.choice(users)["id"],
                legoset_id=legoset["id"],
                legoset_name=legoset["name"]
            )
            comments_count += 1
    print(f"Created {comments_count} comments")

    print("\nCreating auctions and bids...")
    auctions_count = 0
    bids_count = 0
    for legoset in legosets:
        # 30% chance of having an auction
        if random.random() < 0.3:
            auction = create_auction(
                legoset_id=legoset["id"],
                seller_id=legoset.get("owner_id") or random.choice(users)["id"]
            )
            auctions_count += 1

            # Create 0-10 bids per auction
            bid_count = random.randint(0, 10)
            current_price = auction["base_price"]
            for _ in range(bid_count):
                bid = create_bid(
                    auction_id=auction["id"],
                    bidder_id=random.choice(users)["id"],
                    current_price=current_price
                )
                current_price = bid["amount"]
                bids_count += 1

    print(f"Created {auctions_count} auctions and {bids_count} bids")
    print("\nDatabase population completed!")

if __name__ == "__main__":
    populate_database()