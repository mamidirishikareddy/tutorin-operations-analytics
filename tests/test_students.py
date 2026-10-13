import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

transport = ASGITransport(app=app)

@pytest.mark.asyncio
async def test_create_student():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/students/", json={
            "name": "Test User",
            "class_level": "10th",
            "house_number": "123A",
            "contact": "9876543210",
            "joining_date": "2024-06-01"
        })
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["name"] == "Test User"
    assert data["class_level"] == "10th"
