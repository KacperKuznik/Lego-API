import redis
from dotenv import load_dotenv
import os

load_dotenv()

REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT", "redis")
REDIS_KEY = os.getenv("REDIS_KEY")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

r = None

try:
    # If a password is provided, assume a managed/secure Redis instance.
    if REDIS_KEY:
        r = redis.Redis(
            host=REDIS_ENDPOINT,
            port=REDIS_PORT,
            password=REDIS_KEY,
            ssl=True,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )
    else:
        # Fallback to in-cluster Redis without auth (for local/k8s testing)
        r = redis.Redis(
            host=REDIS_ENDPOINT,
            port=REDIS_PORT,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )

    # Test the connection
    r.ping()
    print("Successfully connected to Redis at", REDIS_ENDPOINT)

except redis.AuthenticationError:
    print("Authentication failed. Check your Redis key.")
    raise
except Exception as e:
    print(f"Connection failed: {e}")
    raise

# Export a stable name for the rest of the codebase
redis_client = r
