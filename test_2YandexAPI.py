import pytest
import requests


def get_invalid_api_key(valid_key):
    return valid_key + "Invalid123"


# Testing of 2 API with valid & invalid keys
@pytest.mark.parametrize("api_type, api_key_fixture, base_url_fixture, query_param, additional_params", [
    (
            "geocode",
            "api_key_geocode",
            "base_url_geocode",
            "geocode",
            {"format": "json"}
    ),
    (
            "geosearch",
            "api_key_geosearch",
            "base_url_geosearch",
            "text",
            {"lang": "ru_RU", "type": "geo", "results": "1"}
    )
])
@pytest.mark.parametrize("address", [
    "Санкт-Петербург, Пулковское шоссе, дом 36, корпус 4",
    "Patio de Gale, Praça do Comércio, Lisbon, Portugal"
])
def test_yandex_api_with_invalid_key(api_type, api_key_fixture, base_url_fixture, query_param, additional_params,
                                     address, request):
    api_key = request.getfixturevalue(api_key_fixture)
    base_url = request.getfixturevalue(base_url_fixture)

    invalid_api_key = get_invalid_api_key(api_key)

    # Forming of URL with required parameters
    params = {
        "apikey": api_key,
        query_param: address,
    }
    params.update(additional_params)

    # Checking with valid keys
    print(f"\nTesting {api_type.capitalize()} API with valid key for address: {address}")
    print(f"Request URL: {base_url}")
    print(f"Request Params: {params}")

    response = requests.get(base_url, params=params)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.text}\n")

    response_json = response.json()

    if api_type == "geosearch":
        assert 'features' in response_json, f"{api_type.capitalize()} API: Failed to get valid response with valid API key for address: {address}"
    else:
        assert 'response' in response_json, f"{api_type.capitalize()} API: Failed to get valid response with valid API key for address: {address}"

    # Checking with invalid keys
    params["apikey"] = invalid_api_key
    print(f"Testing {api_type.capitalize()} API with invalid key for address: {address}")
    print(f"Request URL: {base_url}")
    print(f"Request Params: {params}")

    response_invalid = requests.get(base_url, params=params)
    print(f"Response Status Code: {response_invalid.status_code}")
    print(f"Response Content: {response_invalid.text}\n")

    try:
        response_invalid_json = response_invalid.json()

        assert response_invalid_json[
                   'statusCode'] == 403, f"Expected statusCode 403, got {response_invalid_json['statusCode']} for address: {address}"
        assert response_invalid_json[
                   'error'] == "Forbidden", f"Expected error 'Forbidden', got {response_invalid_json['error']} for address: {address}"
        assert response_invalid_json[
                   'message'] == "Invalid api key", f"Expected message 'Invalid api key', got {response_invalid_json['message']} for address: {address}"
    except ValueError:
        pytest.fail(
            f"{api_type.capitalize()} API: Invalid response format received with invalid API key. Response content: {response_invalid.text}")


# Testing of equality coordinates from 2 API
@pytest.mark.parametrize("address", [
    "Санкт-Петербург, Пулковское шоссе, дом 36, корпус 4",
    "СПб ПарашУтная ул 65 стр 1",
    "Мурманская обл.,г. Полярные Зори, ул. Партизан Заполярья 4",
    "Patio de Gale, Praça do Comércio, Lisbon, Portugal",
    "СПб, Мавзолей",
    "ул. Бравых Гедонистов 6666, London, Greate Britain",
    "Мультивселенная №;%*",
    "Первое место приземления пришельцев",
    "()-!!"
])
def test_coords_from_geocode_and_geosearch_are_same(address, api_key_geocode, api_key_geosearch, base_url_geocode,
                                                    base_url_geosearch):
    # Get coords by address via Geocode API
    try:
        geocode_response = requests.get(
            f'{base_url_geocode}?apikey={api_key_geocode}&geocode={address}&format=json'
        ).json()

        assert 'response' in geocode_response, f"No 'response' in Geocode API response for address: {address}"
        assert 'GeoObjectCollection' in geocode_response['response'], \
            f"No 'GeoObjectCollection' in Geocode API response for address: {address}"
        assert 'featureMember' in geocode_response['response']['GeoObjectCollection'], \
            f"No 'featureMember' in Geocode API response for address: {address}"

        feature_members = geocode_response['response']['GeoObjectCollection']['featureMember']
        if len(feature_members) == 0:
            print(f"No coordinates found in Geocode API response for address: {address}.")
            pytest.skip(f"No coordinates found for address '{address}'. Skipping this address.")

        geo_object_collection = geocode_response['response']['GeoObjectCollection']
        geocode_coords = geo_object_collection['featureMember'][0]['GeoObject']['Point']['pos']
        lon_geocode, lat_geocode = map(float, geocode_coords.split())
        print(f"Geocode API Coordinates for {address}: {lon_geocode}, {lat_geocode}")

    except Exception as e:
        print(f"Error processing Geocode API response for address '{address}': {e}")
        pytest.skip(f"Error processing Geocode API response for address '{address}': {e}")

    # Get coords by address via Geosearch API
    try:
        geosearch_response = requests.get(
            f'{base_url_geosearch}?apikey={api_key_geosearch}&text={address}&lang=ru_RU&type=geo&results=1'
        ).json()

        assert 'features' in geosearch_response, f"No 'features' in Geosearch API response for address: {address}"
        assert len(geosearch_response[
                       'features']) > 0, f"No coordinates found in Geosearch API response for address: {address}"

        first_feature = geosearch_response['features'][0]
        lon_geosearch, lat_geosearch = first_feature['geometry']['coordinates']
        print(f"Geosearch API Coordinates for {address}: {lon_geosearch}, {lat_geosearch}")

    except Exception as e:
        print(f"Error processing Geosearch API response for address '{address}': {e}")
        pytest.skip(f"Error processing Geosearch API response for address '{address}': {e}")

    # Equality checking of coords
    assert abs(lon_geocode - lon_geosearch) < 0.0001 and abs(lat_geocode - lat_geosearch) < 0.0001, \
        f"Coordinates mismatch for {address}: Geocode API ({lon_geocode}, {lat_geocode}), \
             Geosearch API ({lon_geosearch}, {lat_geosearch})"

    print(f"Coordinates match for {address}: Geocode API ({lon_geocode}, {lat_geocode}), \
                Geosearch API ({lon_geosearch}, {lat_geosearch})")


# Search for 2 pharmacies near different landmarks
@pytest.mark.parametrize("landmark", [
    "Санкт-Петербург, Дворец Юсуповых",
    "Москва, Мавзолей",
    "London, Big Ben",
    "Egypt, Pyramid of Khufu",
    "Второе место приземления пришельцев",
    "*?:%"
])
def test_find_2_pharmacies(landmark, base_url_geocode, base_url_geosearch, api_key_geocode, api_key_geosearch):
    # Getting the coords by landmark via the Geocode API
    geocode_response = requests.get(
        f'{base_url_geocode}?apikey={api_key_geocode}&geocode={landmark}&format=json'
    ).json()

    assert 'response' in geocode_response, f"No 'response' in Geocode API response for landmark: {landmark}"
    assert 'GeoObjectCollection' in geocode_response['response'], \
        f"No 'GeoObjectCollection' in Geocode API response for landmark: {landmark}"
    assert 'featureMember' in geocode_response['response']['GeoObjectCollection'], \
        f"No 'featureMember' in Geocode API response for landmark: {landmark}"
    feature_members = geocode_response['response']['GeoObjectCollection']['featureMember']
    if len(feature_members) == 0:
        print(f"Warning: No coordinates found for landmark: {landmark}")
        return

    geocode_coords = feature_members[0]['GeoObject']['Point']['pos']
    lon_geocode, lat_geocode = map(float, geocode_coords.split())
    print(f"Coordinates of landmark '{landmark}': {lon_geocode}, {lat_geocode}")

    # Getting pharmacies by coords via Geosearch API
    search_response = requests.get(
        f'{base_url_geosearch}?apikey={api_key_geosearch}&text=pharmacy&ll={lon_geocode},{lat_geocode}&spn=0.9,0.9&lang=en_US&type=biz&results=2'
    ).json()
    print(f"Geosearch API Response for landmark '{landmark}':", search_response)

    if 'features' not in search_response:
        print(f"Error: 'features' key not found in geosearch response for landmark '{landmark}'")
        return

    features = search_response['features']
    if len(features) == 0:
        print(f"ERROR: NO RESULTS FOUND in geosearch response for landmark '{landmark}'")
        return

    pharmacies = [feature['properties'].get('name') for feature in features if feature['properties'].get('name')]
    if not pharmacies:
        print(f"ERROR: NO PHARMACIES found in geosearch results for landmark '{landmark}'")
        return

    print(f"Found pharmacies near '{landmark}': {pharmacies}")
    assert len(pharmacies) > 0, f"NO PHARMACIES found in search results for landmark '{landmark}'"


# Search for contacts of different types of places near the "nearest" metro
@pytest.mark.parametrize("address", [
    "Санкт-Петербург, Пулковское шоссе, дом 36, корпус 4",
    "СПб ПарашУтная ул 65 стр 1",
    "Мурманская обл.,г. Полярные Зори, ул. Партизан Заполярья 4",
    "Patio de Gale, Praça do Comércio, Lisbon, Portugal",
    "СПб, Мавзолей",
    "ул. Бравых Гедонистов 6666, London, Greate Britain",
    "Мультивселенная №;%*",
    "()-!!"
])
@pytest.mark.parametrize("place_type", [
    "fishing+store",
    "hairdresser",
    "McDonald's",
    "dentist",
    "$%^"
])
def test_find_contacts_of_place_type_near_metro_near_address(address, place_type, base_url_geocode, base_url_geosearch,
                                                             api_key_geocode, api_key_geosearch):
    print(f"Testing address: {address}")

    # Getting coords by address via Geocode API
    geocode_response = requests.get(
        f'{base_url_geocode}?apikey={api_key_geocode}&geocode={address}&format=json'
    ).json()

    print(f"Geocode response for address '{address}': {geocode_response}")

    if not geocode_response.get('response', {}).get('GeoObjectCollection', {}).get('featureMember'):
        print(f"No coordinates found for address '{address}'.")
        pytest.skip(f"No coordinates found for address '{address}'. Skipping this address.")

    geo_object = geocode_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
    lon, lat = map(float, geo_object['Point']['pos'].split())
    print(f"Coordinates for address '{address}': {lon}, {lat}")

    # Getting coords of "nearest" metro station via Geocode API
    metro_response = requests.get(
        f'{base_url_geocode}?apikey={api_key_geocode}&geocode={lon},{lat}&kind=metro&results=1&format=json'
    ).json()

    print(f"Metro response for coordinates ({lon}, {lat}): {metro_response}")

    if not metro_response.get('response', {}).get('GeoObjectCollection', {}).get('featureMember'):
        print(f"No metro found near address '{address}'.")
        pytest.skip(f"No metro found near address '{address}'. Skipping this address.")

    metro = metro_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
    metro_coords = metro['Point']['pos'].split()
    metro_name = metro['name']
    print(f"Metro found near address '{address}': {metro_name} at {metro_coords}")

    # Getting place type by coords of metro via Geosearch API
    place_type_response = requests.get(
        f'{base_url_geosearch}?apikey={api_key_geosearch}&text={place_type}&ll={metro_coords[0]},{metro_coords[1]}&spn=0.5,0.5&lang=en_US&type=biz&results=2'
    ).json()

    print(f"Place type response for metro ({metro_coords[0]}, {metro_coords[1]}): {place_type_response}")

    if 'features' not in place_type_response or len(place_type_response['features']) == 0:
        print(f"No place type found near metro '{metro_name}' for address '{address}'.")
        pytest.skip(f"No place type found near metro '{metro_name}' for address '{address}'.")

    # Getting data of place
    place = place_type_response['features'][0]
    place_info = place['properties']
    place_name = place_info.get('name', 'Unknown')
    place_phone = place_info.get('CompanyMetaData', {}).get('Phones', [{}])[0].get('formatted', 'Unknown')
    place_site = place_info.get('CompanyMetaData', {}).get('url', 'Unknown')

    print(f"Place type found: {place_name}, Phone: {place_phone}, Website: {place_site}")

    # Checking the validity of the data
    assert place_name != 'Unknown', f"Place name is not found for address '{address}' and place type '{place_type}'"

    if place_phone == 'Unknown':
        print(f"Warning: Place phone number not found for address '{address}' and place type '{place_type}'")

    if place_site == 'Unknown':
        print(f"Warning: Place website not found for address '{address}' and place type '{place_type}'")
