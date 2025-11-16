import pytest
from httpx import ASGITransport, AsyncClient
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import User

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
async def test_user():
    """Create a test user"""
    db = TestingSessionLocal()
    try:
        user = User(
            email="test@example.com",
            name="Test User",
            phone_number="010-1234-5678",
            hashed_password=pwd_context.hash("password123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.mark.asyncio
async def test_register_success():
    """Test successful user registration"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "name": "New User",
                "phone_number": "010-9876-5432",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert "user_id" in data
        assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(test_user):
    """Test registration with duplicate email"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",  # Same as test_user
                "password": "password123",
                "name": "Another User",
                "phone_number": "010-1111-2222",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(test_user):
    """Test successful login"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_invalid_password(test_user):
    """Test login with invalid password"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/login", json={"email": "test@example.com", "password": "wrongpassword"})

        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user():
    """Test login with non-existent user"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/login", json={"email": "nonexistent@example.com", "password": "password123"}
        )

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(test_user):
    """Test getting current user info when authenticated"""
    # First login to get token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_response = await client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
        token = login_response.json()["access_token"]

        # Then get user info
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"


@pytest.mark.asyncio
async def test_get_me_unauthenticated():
    """Test getting current user info without authentication"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/auth/me")

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token():
    """Test getting current user info with invalid token"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/auth/me", headers={"Authorization": "Bearer invalid_token_here"})

        assert response.status_code == 401
