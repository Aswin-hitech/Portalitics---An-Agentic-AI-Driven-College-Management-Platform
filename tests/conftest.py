import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ["APP_ENV"] = "testing"
os.environ["APP_SECRET_KEY"] = "test_secret_key_for_portalitics_2026"

import pytest
import mongomock
from app.services.mongo_client import mongo_client

@pytest.fixture(autouse=True)
def mock_mongo_db():
    """
    Isolate the test suite from the live/remote MongoDB database
    by forcing mongo_client to use a clean mongomock database for every test.
    """
    original_client = mongo_client.client
    original_db = mongo_client.db
    original_mocked = mongo_client._mocked
    
    # Redirect mongo_client to use mongomock
    mongo_client.client = mongomock.MongoClient()
    mongo_client.db = mongo_client.client["portalitics_db"]
    mongo_client._mocked = True
    
    # Initialize indexes and seed data
    mongo_client.create_indexes()
    mongo_client.auto_seed()
    
    yield
    
    # Restore original client
    mongo_client.client = original_client
    mongo_client.db = original_db
    mongo_client._mocked = original_mocked
