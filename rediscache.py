import redis
from dotenv import load_dotenv
import os

load_dotenv()

REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT")
REDIS_KEY = os.getenv("REDIS_KEY")
REDIS_PORT = os.getenv("REDIS_PORT")

# Validate configuration
if not REDIS_ENDPOINT or not REDIS_PORT or not REDIS_KEY:
    print("Error: Redis host, port, and key must be configured")
    exit(1)

print()  # Add a new line

try:
    # Create a Redis client using the key for authentication
    r = redis.Redis(
        host=REDIS_ENDPOINT,
        port=REDIS_PORT,
        password=REDIS_KEY,
        ssl=True,
        decode_responses=True,
        socket_timeout=10,
        socket_connect_timeout=10
    )

    # Test the connection
    r.ping()
    print("Successfully connected to Azure Redis Cache!")

except redis.AuthenticationError:
    print("Authentication failed. Check your Redis key.")
except Exception as e:
    print(f"Connection failed: {e}")