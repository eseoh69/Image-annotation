from broker.topics import ANNOTATION_STORED, EMBEDDING_CREATED
from broker.redis_broker import RedisBroker
from event_generator.generator import EventGenerator
import json

class EmbeddingService:
    """Listens to annotation.stored, creates embeddings, emits embedding.created."""

    def __init__(self, broker: RedisBroker):
        self.broker = broker
        self.gen = EventGenerator()

    def handle_annotation_stored(self, message):
        data = json.loads(message["data"])
        image_id = data["payload"]["image_id"]
        # Simulate embedding creation (real model provided next week)
        event = self.gen.embedding_created(image_id)
        self.broker.publish(EMBEDDING_CREATED, event)

    def start(self):
        self.broker.subscribe(ANNOTATION_STORED, self.handle_annotation_stored)
        self.broker.listen()