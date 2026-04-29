import json
import numpy as np
from broker.topics import ANNOTATION_STORED, EMBEDDING_CREATED
from broker.redis_broker import RedisBroker
from event_generator.generator import EventGenerator
from db.vector_index import VectorIndex

class EmbeddingService:
    """
    Listens to annotation.stored.
    Simulates an embedding vector from detected object labels.
    Stores vector in FAISS.
    Publishes embedding.created.
    """

    def __init__(self, broker: RedisBroker):
        self.broker = broker
        self.gen = EventGenerator()
        self.index = VectorIndex(dim=128)
        self.seen_events = set()

    def _simulate_embedding(self, objects: list) -> list:
        """
        Simulate an embedding vector from detected objects.
        In production this would be a real image encoder.
        We use object label hashes to create a deterministic vector.
        """
        np.random.seed(abs(hash(str(sorted([o["label"] for o in objects])))) % (2**31))
        vector = np.random.rand(128).astype(np.float32)
        # Normalize to unit vector
        vector = vector / np.linalg.norm(vector)
        return vector.tolist()

    def handle_annotation_stored(self, message):
        try:
            data = json.loads(message["data"])
            event_id = data.get("event_id")

            # Idempotency check
            if event_id in self.seen_events:
                print(f"[Embedding] Duplicate event ignored: {event_id}")
                return
            self.seen_events.add(event_id)

            image_id = data["payload"]["image_id"]

            # Get objects from annotation service via document DB
            from db.document_db import DocumentDB
            db = DocumentDB()
            annotation = db.get_annotation(image_id)
            objects = annotation.get("objects", []) if annotation else []

            # Simulate embedding
            vector = self._simulate_embedding(objects)
            print(f"[Embedding] Created vector for {image_id} ({len(objects)} objects)")

            # Store in FAISS
            self.index.add(image_id, vector)

            # Publish embedding.created
            event = self.gen.embedding_created(image_id)
            self.broker.publish(EMBEDDING_CREATED, event)

        except Exception as e:
            print(f"[Embedding] ERROR: {e}")

    def start(self):
        self.broker.subscribe(ANNOTATION_STORED, self.handle_annotation_stored)
        self.broker.listen()
        print("[Embedding] Listening for annotation.stored events...")