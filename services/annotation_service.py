import json
from broker.topics import INFERENCE_COMPLETED, ANNOTATION_STORED
from broker.redis_broker import RedisBroker
from event_generator.generator import EventGenerator
from db.document_db import DocumentDB

class AnnotationService:
    """
    Listens to inference.completed.
    Saves annotation to MongoDB Atlas.
    Publishes annotation.stored.
    """

    def __init__(self, broker: RedisBroker):
        self.broker = broker
        self.gen = EventGenerator()
        self.db = DocumentDB()
        self.seen_events = set()

    def handle_inference_completed(self, message):
        try:
            data = json.loads(message["data"])
            event_id = data.get("event_id")

            # Idempotency check
            if event_id in self.seen_events:
                print(f"[Annotation] Duplicate event ignored: {event_id}")
                return
            self.seen_events.add(event_id)

            image_id = data["payload"]["image_id"]
            objects = data["payload"]["objects"]

            # Save to MongoDB
            self.db.insert_annotation(image_id, objects)
            print(f"[Annotation] Saved to MongoDB: {image_id} ({len(objects)} objects)")

            # Publish annotation.stored
            event = self.gen.annotation_stored(image_id)
            self.broker.publish(ANNOTATION_STORED, event)

        except Exception as e:
            print(f"[Annotation] ERROR: {e}")

    def start(self):
        self.broker.subscribe(INFERENCE_COMPLETED, self.handle_inference_completed)
        self.broker.listen()
        print("[Annotation] Listening for inference.completed events...")