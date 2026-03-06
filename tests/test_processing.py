import pytest
from mswia.processing.text_processor import normalize_text, Deduplicator

def test_normalize_text_whitespace():
    raw = "  Hello   world! \n  This is a   test.  "
    expected = "Hello world! This is a test."
    assert normalize_text(raw) == expected

def test_normalize_text_empty():
    assert normalize_text("") == ""
    assert normalize_text(None) == ""

def test_deduplicator_basic():
    deduper = Deduplicator()
    assert deduper.is_duplicate("yt", "vid1", "user1", "this is text") is False
    # Exact duplicate
    assert deduper.is_duplicate("yt", "vid1", "user1", "this is text") is True

def test_deduplicator_prefix_match():
    deduper = Deduplicator()
    text1 = "A very long message that is more than fifty characters long..."
    text2 = "A very long message that is more than fifty characters long but different later"
    
    assert deduper.is_duplicate("yt", "vid1", "user1", text1) is False
    # Prefix matches first 50 chars, so it should be considered a duplicate
    assert deduper.is_duplicate("yt", "vid1", "user1", text2) is True

def test_deduplicator_different_author():
    deduper = Deduplicator()
    assert deduper.is_duplicate("yt", "vid1", "user1", "text") is False
    assert deduper.is_duplicate("yt", "vid1", "user2", "text") is False
