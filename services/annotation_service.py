from broker.topics import INFERENCE_COMPLETED, ANNOTATION_STORED
from broker.redis_broker import RedisBroker
from event_generator.generator import EventGenerator
import json

class AnnotationService:
    """Listens to inference.completed, stores annotations, emits annotation.stored."""

    def __init__(self, broker: RedisBroker):
        self.broker = broker
        self.gen = EventGenerator()
        self.store = {}  # placeholder for document DB

    def handle_inference_completed(self, message):
        data = json.loads(message["data"])
        image_id = data["payload"]["image_id"]
        # Simulate storing annotation
        self.store[image_id] = data["payload"]
        event = self.gen.annotation_stored(image_id)
        self.broker.publish(ANNOTATION_STORED, event)

    def start(self):
        self.broker.subscribe(INFERENCE_COMPLETED, self.handle_inference_completed)
        self.broker.listen()