import datetime
import logging
import azure.functions as func
from azure.cosmos import CosmosClient, exceptions
import os

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("COSMOS_DATABASE_NAME")
AUCTIONS_CONTAINER = "auctions"
BIDS_CONTAINER = "bids"

def main(timer: func.TimerRequest) -> None:
    logging.info('Starting auction closing function...')

    client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
    database = client.get_database_client(DATABASE_NAME)
    auctions_container = database.get_container_client(AUCTIONS_CONTAINER)
    bids_container = database.get_container_client(BIDS_CONTAINER)

    now = datetime.datetime.utcnow().isoformat()

    # Get open auctions that should be closed
    query = f"SELECT * FROM c WHERE c.status='open' AND c.close_date < '{now}'"
    open_auctions = list(auctions_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

    logging.info(f"Found {len(open_auctions)} auctions to close.")

    for auction in open_auctions:
        auction_id = auction["id"]
        legoset_id = auction["legoset_id"]

        # Find the highest bid for this auction
        bid_query = f"SELECT * FROM c WHERE c.auction_id='{auction_id}' ORDER BY c.amount DESC"
        bids = list(bids_container.query_items(
            query=bid_query,
            enable_cross_partition_query=True
        ))

        if bids:
            winner = bids[0]
            auction["winner_id"] = winner["bidder_id"]
            auction["winning_bid"] = winner["amount"]
        else:
            auction["winner_id"] = None
            auction["winning_bid"] = None

        # Update auction fields
        auction["status"] = "closed"
        auction["closed_at"] = datetime.datetime.utcnow().isoformat()

        # Save the updated auction
        auctions_container.replace_item(item=auction["id"], body=auction)

        logging.info(f"Auction {auction_id} closed. Winner: {auction.get('winner_id')}")

    logging.info("Auction closing process finished.")
