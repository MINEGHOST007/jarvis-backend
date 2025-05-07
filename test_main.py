import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_read_root():
    """Test the health check endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

@pytest.mark.asyncio
async def test_list_recordings_missing_param():
    """Test /list endpoint with missing user_id param."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/list")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_file_url_missing_param():
    """Test /get_file_url endpoint with missing file_key param."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/get_file_url")
    assert response.status_code == 422

@pytest.mark.asyncio
@patch("main.egress_manager", new_callable=AsyncMock)
async def test_start_egress_invalid(mock_egress_manager):
    """Test /egress/start with mocked egress_manager and invalid input."""
    mock_egress_manager.start_room_composite.side_effect = Exception("fail")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/egress/start", params={"user_id": "test", "room_name": "testroom"})
    assert response.status_code == 500
    assert "detail" in response.json()

@pytest.mark.asyncio
@patch("main.egress_manager", new_callable=AsyncMock)
async def test_stop_egress_invalid(mock_egress_manager):
    """Test /egress/stop with mocked egress_manager and invalid input."""
    mock_egress_manager.stop_egress.side_effect = Exception("fail")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/egress/stop", params={"egress_id": "fakeid"})
    assert response.status_code == 500
    assert "detail" in response.json()

@pytest.mark.asyncio
@patch("main.get_all_files", return_value=["sessions/test/file1.mp4"])
async def test_list_recordings_success(mock_get_all_files):
    """Test /list endpoint with valid user_id."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/list", params={"user_id": "test"})
    assert response.status_code == 200
    assert "recordings" in response.json()
    assert response.json()["recordings"] == ["sessions/test/file1.mp4"]

@pytest.mark.asyncio
@patch("main.get_file_url", return_value="https://example.com/file.mp4")
async def test_get_file_url_success(mock_get_file_url):
    """Test /get_file_url endpoint with valid file_key."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/get_file_url", params={"file_key": "sessions/test/file1.mp4"})
    assert response.status_code == 200
    assert "url" in response.json()
    assert response.json()["url"] == "https://example.com/file.mp4"
