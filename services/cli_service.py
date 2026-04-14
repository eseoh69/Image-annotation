from broker.topics import IMAGE_SUBMITTED, EMBEDDING_CREATED
from broker.redis_broker import RedisBroker
from event_generator.generator import EventGenerator
import json

class CLIService:
    """Simulates user uploads and listens for query results."""

    def __init__(self, broker: RedisBroker):
        self.broker = broker
        self.gen = EventGenerator()

    def submit_image(self, image_id: str):
        event = self.gen.image_submitted(image_id)
        self.broker.publish(IMAGE_SUBMITTED, event)
        print(f"[CLI] Submitted image: {image_id}")
        return event

    def handle_embedding_created(self, message):
        data = json.loads(message["data"])
        print(f"[CLI] Pipeline complete for: {data['payload']['image_id']}")

    def start(self):
        self.broker.subscribe(EMBEDDING_CREATED, self.handle_embedding_created)
        self.broker.listen()