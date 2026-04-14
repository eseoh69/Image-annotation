from broker.topics import IMAGE_SUBMITTED, INFERENCE_COMPLETED
from broker.redis_broker import RedisBroker
from event_generator.generator import EventGenerator
import json

class InferenceService:
    """Listens to image.submitted, simulates object detection, emits inference.completed."""

    def __init__(self, broker: RedisBroker):
        self.broker = broker
        self.gen = EventGenerator()

    def handle_image_submitted(self, message):
        data = json.loads(message["data"])
        image_id = data["payload"]["image_id"]
        event = self.gen.inference_completed(image_id)
        self.broker.publish(INFERENCE_COMPLETED, event)

    def start(self):
        self.broker.subscribe(IMAGE_SUBMITTED, self.handle_image_submitted)
        self.broker.listen()