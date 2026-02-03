import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture()
def client():
    """
    Shared TestClient for all API tests.
    Pytest will auto-discover this fixture.
    """
    return TestClient(app)
