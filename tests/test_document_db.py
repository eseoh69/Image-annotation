import pytest
from unittest.mock import MagicMock, patch
from db.document_db import DocumentDB

def make_mock_db():
    """Create a DocumentDB instance with a mocked MongoDB collection."""
    with patch("db.document_db.MongoClient") as mock_client:
        db = DocumentDB()
        db.collection = {}  # use plain dict as fake collection
        return db

# ─── Helper to simulate MongoDB-like dict collection ───────────

class FakeCollection:
    def __init__(self):
        self.data = {}

    def create_index(self, *args, **kwargs):
        pass

    def insert_one(self, doc):
        self.data[doc["image_id"]] = doc

    def find_one(self, query, projection=None):
        image_id = query.get("image_id")
        doc = self.data.get(image_id)
        if doc and query.get("deleted") is False and doc.get("deleted") is True:
            return None
        if doc and query.get("deleted") is False and doc.get("deleted") is False:
            return doc
        return doc

    def update_one(self, query, update):
        image_id = query.get("image_id")
        if image_id in self.data:
            if "$set" in update:
                self.data[image_id].update(update["$set"])
            if "$push" in update:
                for key, val in update["$push"].items():
                    self.data[image_id].setdefault(key, []).append(val)
        result = MagicMock()
        result.modified_count = 1
        return result

    def find(self, query, projection=None):
        return [doc for doc in self.data.values() if not doc.get("deleted")]


@pytest.fixture
def db():
    with patch("db.document_db.MongoClient"):
        instance = DocumentDB()
        instance.collection = FakeCollection()
        return instance


def test_insert_annotation(db):
    doc = db.insert_annotation("img_001", [{"label": "car", "conf": 0.93}])
    assert doc["image_id"] == "img_001"
    assert doc["deleted"] == False

def test_get_annotation(db):
    db.insert_annotation("img_001", [])
    doc = db.get_annotation("img_001")
    assert doc is not None
    assert doc["image_id"] == "img_001"

def test_soft_delete(db):
    db.insert_annotation("img_001", [])
    db.soft_delete("img_001")
    doc = db.get_annotation("img_001")
    assert doc is None or doc.get("deleted") == True

def test_soft_delete_does_not_hard_delete(db):
    db.insert_annotation("img_001", [])
    db.soft_delete("img_001")
    assert "img_001" in db.collection.data

def test_update_annotation(db):
    db.insert_annotation("img_001", [])
    db.update_annotation("img_001", {"review": {"status": "corrected", "notes": ["car -> truck"]}})
    doc = db.collection.data["img_001"]
    assert doc["review"]["status"] == "corrected"

def test_get_all_active_excludes_deleted(db):
    db.insert_annotation("img_001", [])
    db.insert_annotation("img_002", [])
    db.soft_delete("img_001")
    active = db.get_all_active()
    assert len(active) == 1
    assert active[0]["image_id"] == "img_002"

def test_history_updated_on_correction(db):
    db.insert_annotation("img_001", [])
    db.update_annotation("img_001", {})
    doc = db.collection.data["img_001"]
    assert "annotation.corrected" in doc["history"]