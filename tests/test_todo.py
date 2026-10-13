import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

transport = ASGITransport(app=app)

@pytest.mark.asyncio
async def test_create_todo():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a student first
        student_resp = await ac.post("/students/", json={
            "name": "Todo Tester",
            "class_level": "9th",
            "house_number": "B12",
            "contact": "9123456789",
            "joining_date": "2024-06-15"
        })
        student_id = student_resp.json()["id"]

        # Now create ToDo
        response = await ac.post("/todo/", json={
            "student_id": student_id,
            "title": "Revise Chapter 1",
            "due_date": "2024-06-25"
        })
        assert response.status_code in [200, 201]
