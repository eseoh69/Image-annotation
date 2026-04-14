import random
import uuid
from datetime import datetime, timezone

class EventGenerator:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)

    def _make_event(self, topic: str, payload: dict) -> dict:
        return {
            "type": "publish",
            "topic": topic,
            "event_id": f"evt_{self.rng.randint(1000, 9999)}",
            "payload": {
                **payload,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    def image_submitted(self, image_id=None):
        image_id = image_id or f"img_{self.rng.randint(1000, 9999)}"
        return self._make_event("image.submitted", {
            "image_id": image_id,
            "path": f"images/{image_id}.jpg",
            "source": f"camera_{self.rng.choice(['A','B','C'])}"
        })

    def inference_completed(self, image_id):
        return self._make_event("inference.completed", {
            "image_id": image_id,
            "objects": [
                {"label": "car", "bbox": [12, 44, 188, 200], "conf": round(self.rng.uniform(0.7, 0.99), 2)},
                {"label": "person", "bbox": [230, 51, 286, 210], "conf": round(self.rng.uniform(0.7, 0.99), 2)}
            ]
        })

    def annotation_stored(self, image_id):
        return self._make_event("annotation.stored", {
            "image_id": image_id,
            "status": "stored"
        })

    def embedding_created(self, image_id):
        return self._make_event("embedding.created", {
            "image_id": image_id,
            "vector_id": f"vec_{self.rng.randint(1000, 9999)}"
        })

    def malformed_event(self):
        """Returns a bad event for testing rejection."""
        return {"bad_field": "no topic or event_id here"}

    def duplicate_event(self, event):
        """Returns an exact copy of an event to simulate duplicates."""
        return event.copy()