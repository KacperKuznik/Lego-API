from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv
import os

load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

database = client.create_database_if_not_exists(
    id=DATABASE_NAME,
    offer_throughput=1000
)

containers = ["users", "legosets", "comments", "auctions", "bids"]

for container_name in containers:
    database.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path="/pk")
    )
    
print("Successfully created database")
    