import os
import sys
from datetime import datetime, timedelta

# Setup environment
os.environ['COSMOS_ENDPOINT'] = 'your-cosmos-endpoint'
os.environ['COSMOS_KEY'] = 'your-cosmos-key' 
os.environ['DATABASE_NAME'] = 'your-database-name'

# Add functions to path
sys.path.append('functions/close_auctions')

from __init__ import close_expired_auctions

if __name__ == "__main__":
    print("Testing auction closure directly...")
    results = close_expired_auctions()
    print(f"Closed {len(results)} auctions")