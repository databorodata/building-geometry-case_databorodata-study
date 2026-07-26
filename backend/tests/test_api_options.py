import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Config
from app.db import apply_schema
from app.server import create_app


@pytest.fixture
async def client():
    config = Config(log_level="DEBUG", debug=True, allowed_origins="*")
    app = create_app(config)
    try:
        await app.state.db_pool.open(wait=True, timeout=2.0)
        await apply_schema(app.state.db_pool)
    except Exception:
        await app.state.db_pool.close()
        pytest.skip("database is not available")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client
    await app.state.db_pool.close()


async def create_test_site(client, polygon):
    response = await client.post("/api/v1/sites", json={"name": "test", "polygon": polygon})
    assert response.status_code == 201
    return response.json()


async def test_create_site_returns_root_option(client, rectangle_site):
    body = await create_test_site(client, rectangle_site)
    assert body["site"]["name"] == "test"
    root = body["root_option"]
    assert root["parent_id"] is None
    assert root["result"]["status"] == "ok"
    assert root["params"]["setback_m"] == 3.0


async def test_create_site_rejects_bad_polygon(client):
    payload = {"name": "bad", "polygon": [[0, 0], [10, 10], [10, 0], [0, 10]]}
    response = await client.post("/api/v1/sites", json=payload)
    assert response.status_code == 422


async def test_branch_option_and_list_tree(client, rectangle_site):
    body = await create_test_site(client, rectangle_site)
    site_id = body["site"]["id"]
    root = body["root_option"]
    branch_params = dict(root["params"])
    branch_params["setback_m"] = 5.0
    response = await client.post(
        f"/api/v1/sites/{site_id}/options",
        json={"parent_id": root["id"], "name": "wider setback", "params": branch_params},
    )
    assert response.status_code == 201
    branch = response.json()
    assert branch["parent_id"] == root["id"]
    assert branch["params"]["setback_m"] == 5.0
    response = await client.get(f"/api/v1/sites/{site_id}/options")
    assert response.status_code == 200
    options = response.json()
    assert len(options) == 2
    assert {option["id"] for option in options} == {root["id"], branch["id"]}


async def test_branch_recomputes_result_on_server(client, rectangle_site):
    body = await create_test_site(client, rectangle_site)
    site_id = body["site"]["id"]
    root = body["root_option"]
    branch_params = dict(root["params"])
    branch_params["setback_m"] = 5.0
    response = await client.post(
        f"/api/v1/sites/{site_id}/options",
        json={"parent_id": root["id"], "params": branch_params},
    )
    branch = response.json()
    assert branch["result"]["buildings"][0]["contour_area_m2"] == pytest.approx(30 * 15, rel=0.01)


async def test_compare_options(client, rectangle_site):
    body = await create_test_site(client, rectangle_site)
    site_id = body["site"]["id"]
    root = body["root_option"]
    branch_params = dict(root["params"])
    branch_params["setback_m"] = 5.0
    response = await client.post(
        f"/api/v1/sites/{site_id}/options",
        json={"parent_id": root["id"], "params": branch_params},
    )
    branch = response.json()
    response = await client.get(f"/api/v1/options/{root['id']}/compare/{branch['id']}")
    assert response.status_code == 200
    comparison = response.json()
    assert comparison["left"]["id"] == root["id"]
    assert comparison["right"]["id"] == branch["id"]
    assert comparison["delta"]["footprint_area_m2"] < 0


async def test_get_sites_and_single_site(client, rectangle_site):
    body = await create_test_site(client, rectangle_site)
    site_id = body["site"]["id"]
    response = await client.get("/api/v1/sites")
    assert response.status_code == 200
    assert site_id in [site["id"] for site in response.json()]
    response = await client.get(f"/api/v1/sites/{site_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "test"
    response = await client.get("/api/v1/sites/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


async def test_get_option_returns_snapshot(client, rectangle_site):
    body = await create_test_site(client, rectangle_site)
    root = body["root_option"]
    response = await client.get(f"/api/v1/options/{root['id']}")
    assert response.status_code == 200
    assert response.json()["params"] == root["params"]


async def test_cross_site_references_rejected(client, rectangle_site, notched_site):
    site_a = await create_test_site(client, rectangle_site)
    site_b = await create_test_site(client, notched_site)
    response = await client.post(
        f"/api/v1/sites/{site_a['site']['id']}/options",
        json={"parent_id": site_b["root_option"]["id"], "params": site_a["root_option"]["params"]},
    )
    assert response.status_code == 404


async def test_compare_across_sites_rejected(client, rectangle_site, notched_site):
    site_a = await create_test_site(client, rectangle_site)
    site_b = await create_test_site(client, notched_site)
    response = await client.get(f"/api/v1/options/{site_a['root_option']['id']}/compare/{site_b['root_option']['id']}")
    assert response.status_code == 422


async def test_missing_option_returns_404(client):
    response = await client.get("/api/v1/options/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


async def test_compare_option_with_itself(client, rectangle_site):
    body = await create_test_site(client, rectangle_site)
    root_id = body["root_option"]["id"]
    response = await client.get(f"/api/v1/options/{root_id}/compare/{root_id}")
    assert response.status_code == 200
    delta = response.json()["delta"]
    assert all(value == 0 for value in delta.values())
