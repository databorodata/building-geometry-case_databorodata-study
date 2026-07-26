import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Config
from app.server import create_app


@pytest.fixture
def app():
    config = Config(log_level="DEBUG", debug=True, allowed_origins="*")
    return create_app(config)


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client


async def test_preview_default(client, rectangle_site):
    response = await client.post("/api/v1/massing/preview", json={"polygon": rectangle_site})
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["status"] == "ok"
    assert body["params"]["setback_m"] == 3.0
    assert body["result"]["metrics"]["building_count"] == 1


async def test_preview_with_params(client, notched_site):
    payload = {"polygon": notched_site, "params": {"setback_m": 4.0, "buildings": []}}
    response = await client.post("/api/v1/massing/preview", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["metrics"]["building_count"] == 2
    assert len(body["params"]["buildings"]) == 2


async def test_preview_rejects_bad_polygon(client):
    payload = {"polygon": [[0, 0], [10, 10], [10, 0], [0, 10]]}
    response = await client.post("/api/v1/massing/preview", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_polygon"


async def test_preview_accepts_closing_point_and_floats(client):
    polygon = [[0.0, 0.0], [40.5, 0.0], [40.5, 25.5], [0.0, 25.5], [0.0, 0.0]]
    response = await client.post("/api/v1/massing/preview", json={"polygon": polygon})
    assert response.status_code == 200
    assert response.json()["result"]["metrics"]["building_count"] == 1


async def test_preview_fit_command_roundtrip(client, rectangle_site):
    response = await client.post("/api/v1/massing/preview", json={"polygon": rectangle_site})
    params = response.json()["params"]
    params["fit_gfa_m2"] = 4000
    response = await client.post("/api/v1/massing/preview", json={"polygon": rectangle_site, "params": params})
    assert response.status_code == 200
    body = response.json()
    assert body["params"]["fit_gfa_m2"] is None
    assert body["result"]["metrics"]["gfa_m2"] == pytest.approx(4000.0, rel=0.01)


async def test_preview_rejects_too_small_site(client):
    payload = {"polygon": [[0, 0], [3, 0], [3, 3], [0, 3]]}
    response = await client.post("/api/v1/massing/preview", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "site_too_small"


def test_openapi_lists_routes(app):
    schema = app.openapi()
    assert "/api/v1/massing/preview" in schema["paths"]
    assert "/api/v1/sites" in schema["paths"]
    assert "/api/v1/options/{option_id}/compare/{other_id}" in schema["paths"]
