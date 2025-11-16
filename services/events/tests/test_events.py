from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Event

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_events.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create test database before each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
async def sample_event():
    """Create a sample event for testing"""
    db = TestingSessionLocal()
    try:
        event = Event(
            title="BTS World Tour 2024",
            description="BTS concert in Seoul",
            category="concert",
            venue="Olympic Stadium",
            location="Seoul, South Korea",
            start_date=datetime.now() + timedelta(days=30),
            end_date=datetime.now() + timedelta(days=30, hours=3),
            min_price=150000.0,
            max_price=500000.0,
            total_seats=50000,
            available_seats=50000,
            status="published",
            image_url="https://example.com/bts.jpg",
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    finally:
        db.close()


@pytest.mark.asyncio
async def test_create_event():
    """Test creating a new event"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        event_data = {
            "title": "Coldplay Live in Seoul",
            "description": "Coldplay Music of the Spheres Tour",
            "category": "concert",
            "venue": "Gocheok Sky Dome",
            "location": "Seoul, South Korea",
            "start_date": (datetime.now() + timedelta(days=60)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=60, hours=3)).isoformat(),
            "min_price": 120000.0,
            "max_price": 350000.0,
            "total_seats": 25000,
            "image_url": "https://example.com/coldplay.jpg",
        }

        response = await client.post("/events", json=event_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Coldplay Live in Seoul"
        assert data["category"] == "concert"
        assert data["total_seats"] == 25000
        assert data["available_seats"] == 25000
        assert data["status"] == "draft"
        assert "event_id" in data


@pytest.mark.asyncio
async def test_get_events_list(sample_event):
    """Test getting list of events"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/events")

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) >= 1
        assert data["total"] >= 1
        assert data["events"][0]["title"] == "BTS World Tour 2024"


@pytest.mark.asyncio
async def test_get_events_by_category(sample_event):
    """Test filtering events by category"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/events?category=concert")

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) >= 1
        assert all(event["category"] == "concert" for event in data["events"])


@pytest.mark.asyncio
async def test_get_event_by_id(sample_event):
    """Test getting a specific event by ID"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/events/{sample_event.event_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == sample_event.event_id
        assert data["title"] == "BTS World Tour 2024"
        assert data["venue"] == "Olympic Stadium"


@pytest.mark.asyncio
async def test_get_nonexistent_event():
    """Test getting a non-existent event"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/events/nonexistent_id")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_event(sample_event):
    """Test updating an event"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        update_data = {"title": "BTS World Tour 2024 - Updated", "min_price": 180000.0, "max_price": 600000.0}

        response = await client.put(f"/events/{sample_event.event_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "BTS World Tour 2024 - Updated"
        assert data["min_price"] == 180000.0
        assert data["max_price"] == 600000.0


@pytest.mark.asyncio
async def test_publish_event(sample_event):
    """Test publishing an event"""
    # First set it to draft
    db = TestingSessionLocal()
    event = db.query(Event).filter(Event.event_id == sample_event.event_id).first()
    event.status = "draft"
    db.commit()
    db.close()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/events/{sample_event.event_id}/publish")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"


@pytest.mark.asyncio
async def test_cancel_event(sample_event):
    """Test cancelling an event"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/events/{sample_event.event_id}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_get_event_seats(sample_event):
    """Test getting seats for an event"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/events/{sample_event.event_id}/seats")

        assert response.status_code == 200
        data = response.json()
        # The response might be empty or contain seat data
        assert isinstance(data, list) or isinstance(data, dict)


@pytest.mark.asyncio
async def test_pagination():
    """Test event list pagination"""
    # Create multiple events
    db = TestingSessionLocal()
    for i in range(15):
        event = Event(
            title=f"Event {i}",
            description=f"Description {i}",
            category="concert",
            venue=f"Venue {i}",
            location="Seoul",
            start_date=datetime.now() + timedelta(days=i),
            end_date=datetime.now() + timedelta(days=i, hours=2),
            min_price=100000.0,
            max_price=200000.0,
            total_seats=1000,
            available_seats=1000,
            status="published",
        )
        db.add(event)
    db.commit()
    db.close()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Get first page
        response = await client.get("/events?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 10
        assert data["total"] == 15

        # Get second page
        response = await client.get("/events?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 5
