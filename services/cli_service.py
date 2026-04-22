import json
import os
import uuid
from broker.topics import IMAGE_SUBMITTED, INFERENCE_COMPLETED
from broker.redis_broker import RedisBroker
from event_generator.generator import EventGenerator

class CLIService:
    """
    User-facing CLI.
    - upload <image_path>: submits a real image into the pipeline
    - query <image_id>: shows detected objects for that image
    """

    def __init__(self, broker: RedisBroker):
        self.broker = broker
        self.gen = EventGenerator()
        self.results = {}  # stores inference results by image_id

    def handle_inference_completed(self, message):
        try:
            data = json.loads(message["data"])
            image_id = data["payload"]["image_id"]
            objects = data["payload"]["objects"]
            self.results[image_id] = objects
            print(f"\n[CLI] ✅ Pipeline complete for: {image_id}")
            print(f"[CLI] Detected objects:")
            for obj in objects:
                print(f"       - {obj['label']} (confidence: {obj['conf']})")
        except Exception as e:
            print(f"[CLI] ERROR handling result: {e}")

    def upload_image(self, image_path: str):
        if not os.path.exists(image_path):
            print(f"[CLI] ERROR: File not found: {image_path}")
            return None

        image_id = f"img_{uuid.uuid4().hex[:8]}"
        event = self.gen.image_submitted(image_id)
        event["payload"]["path"] = image_path
        event["payload"]["image_id"] = image_id

        self.broker.publish(IMAGE_SUBMITTED, event)
        print(f"[CLI] Uploaded: {image_path} → image_id: {image_id}")
        return image_id

    def query(self, image_id: str):
        if image_id in self.results:
            print(f"\n[CLI] Results for {image_id}:")
            for obj in self.results[image_id]:
                print(f"  - {obj['label']} (conf: {obj['conf']})")
        else:
            print(f"[CLI] No results yet for {image_id}")

    def start(self):
        self.broker.subscribe(INFERENCE_COMPLETED, self.handle_inference_completed)
        self.broker.listen()