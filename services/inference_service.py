import json
import os
from broker.topics import IMAGE_SUBMITTED, INFERENCE_COMPLETED
from broker.redis_broker import RedisBroker
from event_generator.generator import EventGenerator
from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # downloads automatically first time

class InferenceService:
    """
    Listens to image.submitted.
    Runs real YOLOv8 object detection on the image.
    Publishes inference.completed with detected object labels.
    """

    def __init__(self, broker: RedisBroker):
        self.broker = broker
        self.gen = EventGenerator()
        self.seen_events = set()  # idempotency

    def handle_image_submitted(self, message):
        try:
            data = json.loads(message["data"])
            event_id = data.get("event_id")

            # Idempotency check
            if event_id in self.seen_events:
                print(f"[Inference] Duplicate event ignored: {event_id}")
                return
            self.seen_events.add(event_id)

            image_id = data["payload"]["image_id"]
            image_path = data["payload"]["path"]

            print(f"[Inference] Running detection on {image_path}...")

            if not os.path.exists(image_path):
                print(f"[Inference] ERROR: Image not found at {image_path}")
                return

            # Run real YOLOv8 detection
            results = model(image_path, verbose=False)
            objects = []
            for result in results:
                for box in result.boxes:
                    label = model.names[int(box.cls)]
                    conf = float(box.conf)
                    bbox = box.xyxy[0].tolist()
                    objects.append({
                        "label": label,
                        "bbox": [round(x, 2) for x in bbox],
                        "conf": round(conf, 2)
                    })

            print(f"[Inference] Detected {len(objects)} objects: {[o['label'] for o in objects]}")

            event = self.gen.inference_completed_real(image_id, objects)
            self.broker.publish(INFERENCE_COMPLETED, event)

        except Exception as e:
            print(f"[Inference] ERROR: {e}")

    def start(self):
        self.broker.subscribe(IMAGE_SUBMITTED, self.handle_image_submitted)
        self.broker.listen()
        print("[Inference] Listening for image.submitted events...")