from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv
import os
import logging

load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")

logger = logging.getLogger(__name__)

client = None
database = None

if COSMOS_ENDPOINT and COSMOS_KEY and DATABASE_NAME:
    try:
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

        logger.info("Successfully created/connected to Cosmos DB database '%s'", DATABASE_NAME)
    except Exception as e:
        # Don't let DB initialization crash the whole app — log and continue.
        logger.exception("Failed to initialize Cosmos DB client: %s", e)
        client = None
        database = None
else:
    logger.warning("COSMOS_ENDPOINT/COSMOS_KEY/DATABASE_NAME not fully set; skipping Cosmos DB initialization")
    