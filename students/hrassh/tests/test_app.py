import pytest

from app import app
from converter import ConversionError, convert


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_length():
    assert convert("length", 1, "km", "m") == 1000


def test_mass():
    assert convert("mass", 1, "kg", "g") == 1000


def test_temperature():
    assert convert("temperature", 100, "C", "F") == 212
    assert convert("temperature", 0, "C", "K") == 273.15


def test_unknown_unit():
    with pytest.raises(ConversionError):
        convert("length", 1, "km", "kg")


def test_below_absolute_zero():
    with pytest.raises(ConversionError):
        convert("temperature", -300, "C", "K")


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Конвертер одиниць" in response.get_data(as_text=True)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_api_convert(client):
    response = client.get("/api/convert?category=length&value=2&from=m&to=cm")
    assert response.status_code == 200
    assert response.get_json()["result"] == 200


def test_api_bad_value(client):
    response = client.get("/api/convert?category=length&value=abc&from=m&to=cm")
    assert response.status_code == 400


def test_api_bad_category(client):
    response = client.get("/api/convert?category=speed&value=1&from=a&to=b")
    assert response.status_code == 400
