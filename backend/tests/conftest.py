import json
import pathlib

import pytest

DATA_DIR = pathlib.Path(__file__).parent.parent.parent / "data" / "sites"


def load_site(name: str) -> list[tuple[float, float]]:
    data = json.loads((DATA_DIR / f"{name}.json").read_text())
    return [(float(x), float(y)) for x, y in data["polygon"]]


@pytest.fixture
def rectangle_site():
    return load_site("rectangle")


@pytest.fixture
def l_shaped_site():
    return load_site("l-shaped")


@pytest.fixture
def notched_site():
    return load_site("notched")
