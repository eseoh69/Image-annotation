from pymongo import MongoClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

class DocumentDB:
    """
    MongoDB Atlas-backed annotation storage.
    Owns the 'annotations' collection.
    No other service reads/writes here directly.
    Uses soft delete — records are never hard deleted.
    """

    def __init__(self):
        uri = os.getenv("MONGO_URI")
        self.client = MongoClient(uri)
        self.db = self.client["ec530"]
        self.collection = self.db["annotations"]
        self.collection.create_index("image_id", unique=True)

    def insert_annotation(self, image_id: str, objects: list, camera: str = "unknown"):
        document = {
            "image_id": image_id,
            "camera": camera,
            "objects": objects,
            "review": {"status": "pending", "notes": []},
            "history": ["annotation.stored"],
            "deleted": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        try:
            self.collection.insert_one(document)
        except Exception:
            pass  # already exists
        return document

    def get_annotation(self, image_id: str):
        return self.collection.find_one(
            {"image_id": image_id, "deleted": False},
            {"_id": 0}
        )

    def update_annotation(self, image_id: str, updates: dict):
        self.collection.update_one(
            {"image_id": image_id},
            {
                "$set": updates,
                "$push": {"history": "annotation.corrected"}
            }
        )
        return self.get_annotation(image_id)

    def soft_delete(self, image_id: str):
        result = self.collection.update_one(
            {"image_id": image_id},
            {"$set": {"deleted": True}}
        )
        return result.modified_count > 0

    def get_all_active(self):
        return list(self.collection.find({"deleted": False}, {"_id": 0}))