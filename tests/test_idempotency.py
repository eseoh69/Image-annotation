from event_generator.generator import EventGenerator

gen = EventGenerator(seed=42)

def test_duplicate_event_same_id():
    """Duplicate events have the same event_id — system should detect this."""
    event = gen.image_submitted("img_001")
    duplicate = gen.duplicate_event(event)
    assert event["event_id"] == duplicate["event_id"]

def test_idempotency_key_is_event_id():
    """event_id is the idempotency key — storing it prevents double processing."""
    seen_ids = set()
    
    # Generate ONE event, then duplicate it 3 times (simulating duplicate delivery)
    original = gen.image_submitted("img_001")
    events = [gen.duplicate_event(original) for _ in range(3)]
    
    processed = []
    for e in events:
        if e["event_id"] not in seen_ids:
            seen_ids.add(e["event_id"])
            processed.append(e)
    assert len(processed) == 1  # only first one processed