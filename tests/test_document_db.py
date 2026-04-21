import pytest
from db.document_db import DocumentDB

@pytest.fixture
def db():
    return DocumentDB()

def test_insert_annotation(db):
    """Inserting an annotation stores it correctly."""
    doc = db.insert_annotation("img_001", [{"label": "car", "conf": 0.93}])
    assert doc["image_id"] == "img_001"
    assert doc["deleted"] == False

def test_get_annotation(db):
    """Can retrieve a stored annotation."""
    db.insert_annotation("img_001", [])
    doc = db.get_annotation("img_001")
    assert doc is not None
    assert doc["image_id"] == "img_001"

def test_soft_delete(db):
    """Soft delete marks document as deleted, does not remove it."""
    db.insert_annotation("img_001", [])
    db.soft_delete("img_001")
    # Should not be retrievable
    assert db.get_annotation("img_001") is None
    # But should still exist in the collection
    assert db.collection["img_001"]["deleted"] == True

def test_soft_delete_does_not_hard_delete(db):
    """Record still exists in collection after soft delete."""
    db.insert_annotation("img_001", [])
    db.soft_delete("img_001")
    assert "img_001" in db.collection

def test_update_annotation(db):
    """Can update fields on an existing annotation."""
    db.insert_annotation("img_001", [])
    db.update_annotation("img_001", {"review": {"status": "corrected", "notes": ["car -> truck"]}})
    doc = db.get_annotation("img_001")
    assert doc["review"]["status"] == "corrected"

def test_get_all_active_excludes_deleted(db):
    """get_all_active only returns non-deleted documents."""
    db.insert_annotation("img_001", [])
    db.insert_annotation("img_002", [])
    db.soft_delete("img_001")
    active = db.get_all_active()
    assert len(active) == 1
    assert active[0]["image_id"] == "img_002"

def test_history_updated_on_correction(db):
    """History trail is updated when annotation is corrected."""
    db.insert_annotation("img_001", [])
    db.update_annotation("img_001", {})
    doc = db.get_annotation("img_001")
    assert "annotation.corrected" in doc["history"]