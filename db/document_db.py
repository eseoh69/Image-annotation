# db/document_db.py
# MongoDB document schema and stub methods
# Real connection will be wired in Week 2

# ----- SCHEMA DESIGN -----
# Each image document looks like this:
# {
#   "image_id": "img_1042",        # unique identifier
#   "camera": "A",                 # source camera
#   "objects": [                   # detected objects (variable length)
#     {"label": "car", "bbox": [12, 44, 188, 200], "conf": 0.93},
#     {"label": "person", "bbox": [230, 51, 286, 210], "conf": 0.88}
#   ],
#   "review": {                    # human correction notes
#     "status": "corrected",
#     "notes": ["car -> truck on 2nd pass"]
#   },
#   "history": ["submitted", "annotation.stored"],  # event trail
#   "deleted": False               # soft delete flag — never hard delete
# }

class DocumentDB:
    """
    Stub for MongoDB annotation storage.
    Owns the 'annotations' collection.
    No other service should read/write here directly.
    Real MongoDB connection wired in Week 2.
    """

    def __init__(self):
        # Week 2: replace with real MongoDB client
        # self.client = MongoClient("mongodb://localhost:27017/")
        # self.db = self.client["ec530"]
        # self.collection = self.db["annotations"]
        self.collection = {}  # placeholder

    def insert_annotation(self, image_id: str, objects: list, camera: str = "unknown"):
        """Store a new annotation document."""
        document = {
            "image_id": image_id,
            "camera": camera,
            "objects": objects,
            "review": {"status": "pending", "notes": []},
            "history": ["annotation.stored"],
            "deleted": False  # soft delete flag
        }
        self.collection[image_id] = document
        return document

    def get_annotation(self, image_id: str):
        """Retrieve annotation by image_id. Returns None if deleted."""
        doc = self.collection.get(image_id)
        if doc and doc.get("deleted") == False:
            return doc
        return None

    def update_annotation(self, image_id: str, updates: dict):
        """Update fields on an existing annotation."""
        if image_id in self.collection:
            self.collection[image_id].update(updates)
            self.collection[image_id]["history"].append("annotation.corrected")
            return self.collection[image_id]
        return None

    def soft_delete(self, image_id: str):
        """
        Soft delete — marks document as deleted instead of removing it.
        Professor explicitly requires this pattern (Lecture 13, Slide 18).
        """
        if image_id in self.collection:
            self.collection[image_id]["deleted"] = True
            return True
        return False

    def get_all_active(self):
        """Return all documents that have not been soft deleted."""
        return [doc for doc in self.collection.values() if not doc.get("deleted")]