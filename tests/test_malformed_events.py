from broker.redis_broker import RedisBroker
from event_generator.generator import EventGenerator
from unittest.mock import MagicMock

gen = EventGenerator(seed=42)

def make_broker():
    broker = RedisBroker.__new__(RedisBroker)
    broker.client = MagicMock()
    broker.pubsub = MagicMock()
    return broker

def test_missing_topic_rejected():
    broker = make_broker()
    event = {"type": "publish", "event_id": "evt_1", "payload": {"timestamp": "2026-01-01T00:00:00Z"}}
    assert broker.publish("image.submitted", event) == False

def test_missing_event_id_rejected():
    broker = make_broker()
    event = {"type": "publish", "topic": "image.submitted", "payload": {"timestamp": "2026-01-01T00:00:00Z"}}
    assert broker.publish("image.submitted", event) == False

def test_missing_timestamp_rejected():
    broker = make_broker()
    event = {"type": "publish", "topic": "image.submitted", "event_id": "evt_1", "payload": {}}
    assert broker.publish("image.submitted", event) == False

def test_empty_event_rejected():
    broker = make_broker()
    assert broker.publish("image.submitted", {}) == False

def test_empty_image_id_rejected():
    """An event with an empty image_id should be rejected."""
    broker = make_broker()
    event = {
        "type": "publish",
        "topic": "image.submitted",
        "event_id": "evt_001",
        "payload": {
            "image_id": "",   # empty — should be rejected
            "path": "images/test.jpg",
            "source": "camera_A",
            "timestamp": "2026-04-14T00:00:00Z"
        }
    }
    result = broker.publish("image.submitted", event)
    assert result == False, "Empty image_id should be rejected"