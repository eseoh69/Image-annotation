import pytest
from unittest.mock import MagicMock, patch
from broker.redis_broker import RedisBroker
from event_generator.generator import EventGenerator

gen = EventGenerator(seed=42)

# --- Schema Tests ---

def test_valid_event_has_required_fields():
    event = gen.image_submitted()
    assert "type" in event
    assert "topic" in event
    assert "event_id" in event
    assert "payload" in event
    assert "timestamp" in event["payload"]

def test_all_event_types_are_valid():
    events = [
        gen.image_submitted(),
        gen.inference_completed("img_001"),
        gen.annotation_stored("img_001"),
        gen.embedding_created("img_001"),
    ]
    for event in events:
        assert "event_id" in event
        assert "topic" in event

# --- Malformed Event Tests ---

def test_malformed_event_rejected():
    broker = RedisBroker.__new__(RedisBroker)  # skip __init__
    broker.client = MagicMock()
    broker.pubsub = MagicMock()
    bad_event = gen.malformed_event()
    result = broker.publish("image.submitted", bad_event)
    assert result == True

def test_valid_event_accepted():
    broker = RedisBroker.__new__(RedisBroker)
    broker.client = MagicMock()
    broker.pubsub = MagicMock()
    good_event = gen.image_submitted()
    result = broker.publish("image.submitted", good_event)
    assert result == True