import json
import uuid
import random
import time

from faker import Faker
from google.cloud import pubsub_v1


fake = Faker()

PROJECT_ID = "YOUR_GCP_PROJECT_ID"
TOPIC_ID = "transaction-topic"


publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)


locations = ["NY", "CA", "TX", "FL", "WA"]

merchants = ["Amazon", "Walmart", "Apple", "Target", "BestBuy"]


def generate_transaction():

    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "card_id": fake.credit_card_number(),
        "merchant": random.choice(merchants),
        "amount": round(random.uniform(1, 2000), 2),
        "location": random.choice(locations),
        "event_time": fake.iso8601()
    }

    return transaction


def serialize_transaction(transaction):
    return json.dumps(transaction).encode("utf-8")


while True:

    transaction = generate_transaction()

    data = serialize_transaction(transaction)

    future = publisher.publish(topic_path, data)

    print("Sent transaction:", transaction)

    time.sleep(1)