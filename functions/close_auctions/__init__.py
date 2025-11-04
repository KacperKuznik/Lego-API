import logging
import os
import json
import azure.functions as func
from azure.cosmos import CosmosClient
from datetime import datetime, timezone

# Initialize Cosmos DB client
cosmos_endpoint = os.environ['COSMOS_ENDPOINT']
cosmos_key = os.environ['COSMOS_KEY']
database_name = os.environ['DATABASE_NAME']

cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
database = cosmos_client.get_database_client(database_name)
auctions_container = database.get_container_client("auctions")
bids_container = database.get_container_client("bids")
users_container = database.get_container_client("users")
legosets_container = database.get_container_client("legosets")

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    
    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info(f'Python timer trigger function for auction closing ran at {utc_timestamp}')
    
    try:
        closed_auctions = close_expired_auctions()
        logging.info(f"Successfully closed {len(closed_auctions)} auctions")
        
    except Exception as e:
        logging.error(f"Error in auction closing function: {str(e)}")
        raise

def close_expired_auctions():
    current_time = datetime.utcnow().isoformat()
    
    # Query for open auctions that have expired
    query = """
    SELECT * FROM c 
    WHERE c.close_date <= @current_time 
    AND c.status = 'open'
    """
    
    parameters = [
        {"name": "@current_time", "value": current_time}
    ]
    
    expired_auctions = list(auctions_container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))
    
    closed_auctions = []
    
    for auction in expired_auctions:
        try:
            # Get the highest bid for this auction
            bid_query = """
            SELECT * FROM c 
            WHERE c.auction_id = @auction_id 
            ORDER BY c.amount DESC OFFSET 0 LIMIT 1
            """
            
            bid_parameters = [
                {"name": "@auction_id", "value": auction['id']}
            ]
            
            highest_bids = list(bids_container.query_items(
                query=bid_query,
                parameters=bid_parameters,
                enable_cross_partition_query=True
            ))
            
            # Update auction status and set winner
            if highest_bids:
                highest_bid = highest_bids[0]
                auction['status'] = 'closed'
                auction['winner_id'] = highest_bid['bidder_id']
                auction['winning_bid'] = highest_bid['amount']
                auction['closed_at'] = datetime.utcnow().isoformat()
                
                # Transfer LegoSet ownership to winner
                transfer_ownership(
                    auction['legoset_id'], 
                    auction['seller_id'], 
                    auction['winner_id']
                )
                
                logging.info(f"Auction {auction['id']} closed. Winner: {auction['winner_id']} with bid: {auction['winning_bid']}")
            else:
                # No bids - mark as closed without winner
                auction['status'] = 'closed'
                auction['closed_at'] = datetime.utcnow().isoformat()
                logging.info(f"Auction {auction['id']} closed with no bids")
            
            # Update auction in database
            auctions_container.replace_item(auction['id'], auction)
            closed_auctions.append(auction)
            
        except Exception as e:
            logging.error(f"Error closing auction {auction['id']}: {str(e)}")
            continue
    
    return closed_auctions

def transfer_ownership(legoset_id: str, seller_id: str, winner_id: str):
    try:
        # Get LegoSet
        legoset = legosets_container.read_item(legoset_id, partition_key='LEGOSET')
        
        # Update owner
        legoset['owner_id'] = winner_id
        legosets_container.replace_item(legoset_id, legoset)
        
        # Update seller's owned_sets
        seller = users_container.read_item(seller_id, partition_key='USER')
        if legoset_id in seller.get('owned_sets', []):
            seller['owned_sets'].remove(legoset_id)
            users_container.replace_item(seller_id, seller)
        
        # Update winner's owned_sets
        winner = users_container.read_item(winner_id, partition_key='USER')
        if 'owned_sets' not in winner:
            winner['owned_sets'] = []
        if legoset_id not in winner['owned_sets']:
            winner['owned_sets'].append(legoset_id)
            users_container.replace_item(winner_id, winner)
            
    except Exception as e:
        logging.error(f"Error transferring ownership for LegoSet {legoset_id}: {str(e)}")
        raise