import pytest

@pytest.fixture(scope="session", autouse=True)
def base_url_geocode():
    return "https://geocode-maps.yandex.ru/1.x"

@pytest.fixture(scope="session", autouse=True)
def base_url_geosearch():
    return "https://search-maps.yandex.ru/v1"

@pytest.fixture(scope="session", autouse=True)
def api_key_geocode():
    return "b6406238-38e9-4bc0-ac07-5bca9de0e327"

@pytest.fixture(scope="session", autouse=True)
def api_key_geosearch():
    return "99d471d5-cb8f-4d4e-b915-6fb3717e217b"
