import redis
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisBroker:
    def __init__(self, host='localhost', port=6379):
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
        self.pubsub = self.client.pubsub()

    def publish(self, topic: str, event: dict):
        """Publish an event to a topic."""
        if not self._validate_event(event):
            logger.warning(f"Malformed event rejected: {event}")
            return False
        self.client.publish(topic, json.dumps(event))
        logger.info(f"Published to {topic}: {event['event_id']}")
        return True

    def subscribe(self, topic: str, handler):
        """Subscribe to a topic with a handler function."""
        self.pubsub.subscribe(**{topic: handler})
        logger.info(f"Subscribed to {topic}")

    def listen(self):
        """Start listening for messages."""
        self.pubsub.run_in_thread(sleep_time=0.001)

    def _validate_event(self, event: dict) -> bool:
        """Validate that an event has all required fields and non-empty values."""
        required_fields = ["type", "topic", "event_id", "payload"]
        if not all(field in event for field in required_fields):
            return False
        if "timestamp" not in event.get("payload", {}):
            return False
    
        # Check that image_id exists and is not empty if present in payload
        image_id = event.get("payload", {}).get("image_id", None)
        if image_id is not None and str(image_id).strip() == "":
            return False
    
        return True