from broker.topics import IMAGE_SUBMITTED
from broker.redis_broker import RedisBroker
from event_generator.generator import EventGenerator

class UploadService:
    """Receives image uploads and emits image.submitted events."""

    def __init__(self, broker: RedisBroker):
        self.broker = broker
        self.gen = EventGenerator()

    def upload_image(self, image_id: str):
        event = self.gen.image_submitted(image_id)
        self.broker.publish(IMAGE_SUBMITTED, event)
        return event