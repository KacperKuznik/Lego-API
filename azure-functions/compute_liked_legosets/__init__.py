import datetime
import azure.functions as func
from azure.cosmos import CosmosClient
from textblob import TextBlob
import os

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("COSMOS_DATABASE_NAME")

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
db = client.get_database_client(DATABASE_NAME)
comments_container = db.get_container_client("comments")
legosets_container = db.get_container_client("legosets")

def analyze_sentiment(text: str) -> float:
    return TextBlob(text).sentiment.polarity

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    # Get all Lego sets
    legosets = list(legosets_container.query_items(
        query="SELECT * FROM c",
        enable_cross_partition_query=True
    ))

    liked_scores = []

    # Compute sentiment score for each Lego Set
    for legoset in legosets:
        legoset_id = legoset["id"]
        comments = list(comments_container.query_items(
            query=f"SELECT * FROM c WHERE c.legoset_id='{legoset_id}'",
            enable_cross_partition_query=True
        ))

        if not comments:
            continue

        score = sum(analyze_sentiment(c["text"]) for c in comments) / len(comments)
        liked_scores.append({
            "legoset_id": legoset_id,
            "name": legoset["name"],
            "score": score
        })

    # Sort by score descending
    liked_scores.sort(key=lambda x: x["score"], reverse=True)

    print("Top liked Lego Sets:", liked_scores[:10])
