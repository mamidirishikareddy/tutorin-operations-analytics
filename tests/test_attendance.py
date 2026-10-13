import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

transport = ASGITransport(app=app)

@pytest.mark.asyncio
async def test_attendance_checkin():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First create a student
        student_resp = await ac.post("/students/", json={
            "name": "Test User",
            "class_level": "10th",
            "house_number": "123A",
            "contact": "9876543210",
            "joining_date": "2024-06-01"
        })
        student_id = student_resp.json()["id"]

        # Now check-in attendance
        response = await ac.post("/attendance/mark", json={"student_id": student_id, "checkin_time": "2024-06-30T10:00:00"})
        assert response.status_code in [200, 201]
