import requests
import json
from typing import Optional, List, Tuple


"""
    This file includes functions for interaction with RapidAPI and two optional funcs.
"""


def str_to_float(text: str) -> float:
    """
    Func for replacement ',' to '.' in the floating numbers

    :param text: floating number separated with ','
    :return: float
    """
    match = text.replace(',', '.')
    return float(match)


def is_float(number: str) -> bool:
    try:
        float(number)
    except:
        return False
    else:
        return True


def get_city(query: str = 'New York') -> Tuple[Optional[str], Optional[int]]:
    """
    Finds an ID of the destination city.
    """

    url = "https://hotels4.p.rapidapi.com/locations/v2/search"

    querystring = {"query": query, "locale": "ru_RU", "currency": "RUB"}

    headers = {
        "X-RapidAPI-Key": "f373575cfdmshb4ce09d154823d7p19ac62jsn692fb087c1d8",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    j_response = json.loads(response.text)

    with open('found.json', 'w') as file:
        print(json.dumps(j_response, indent=4), file=file)
    if len(j_response['suggestions'][0]['entities']) == 0:
        return None, None
    else:
        match = j_response['suggestions'][0]['entities'][0]['destinationId']

    city_name = j_response['suggestions'][0]['entities'][0]['name']

    return city_name, match


def get_city_hotels(city_id: int, quantity: int = 10, check_in='2022-07-22', check_out='2022-07-23',
                    sort_order='PRICE', min_price=None, max_price=None, distance=None) -> List:
    """
    Forms a query to Hotels.com API with params described below

    :param city_id: ID of the city known from the previous query.
    :param quantity: Number of hotels that have to be shown.
    :param check_in: str. Check in date formatted like 'YYYY-mm-dd'.
    :param check_out: str. Check out date formatted like 'YYYY-mm-dd'.
    :param sort_order: str. Sort order values in the description of the func.
    :param min_price: float. Minimum price in chosen currency.
    :param max_price: float. Maximum price in chosen currency.
    :param distance: float. Distance from the city center in kms.
    :return: Deserialized JSON with useful data in a dict. Or an empty dict.
    """
    #  sort_order values: BEST_SELLER|STAR_RATING_HIGHEST_FIRST|STAR_RATING_LOWEST_FIRST|
    #  DISTANCE_FROM_LANDMARK|GUEST_RATING|PRICE_HIGHEST_FIRST|PRICE

    url = "https://hotels4.p.rapidapi.com/properties/list"

    if min_price is None:
        querystring = {"destinationId": city_id, "pageNumber": "1", "pageSize": quantity, "checkIn": check_in,
                       "checkOut": check_out, "adults1": "2", "sortOrder": sort_order,
                       "locale": "ru_RU", "currency": "RUB"}
    else:
        querystring = {"destinationId": city_id, "pageNumber": "1", "pageSize": quantity, "checkIn": check_in,
                       "checkOut": check_out, "adults1": "2", "sortOrder": sort_order, "locale": "ru_RU",
                       "currency": "RUB", "priceMin": min_price, "priceMax": max_price}

    headers = {
        "X-RapidAPI-Key": "f373575cfdmshb4ce09d154823d7p19ac62jsn692fb087c1d8",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, params=querystring, headers=headers)

    json_response = json.loads(response.text)

    if distance is None:
        hotels_found = json_response['data']['body']['searchResults']['results']

    else:
        hotels_found = []
        for hotel in json_response['data']['body']['searchResults']['results']:
            hotel_dist = str_to_float(hotel['landmarks'][0]['distance'].split(' ')[0])
            if hotel_dist <= distance:
                hotels_found.append(hotel)

    return hotels_found


def get_photos(hotel_id: int, quantity: int = 5) -> Optional[List]:
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    querystring = {"id": hotel_id}

    headers = {
        "X-RapidAPI-Key": "f373575cfdmshb4ce09d154823d7p19ac62jsn692fb087c1d8",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, params=querystring, allow_redirects=True)

    try:
        photos_found = json.loads(response.text)
    except json.decoder.JSONDecodeError:
        photos_found = {}

    if not photos_found.get('hotelImages'):
        return None

    found_urls = []

    for num, image in enumerate(photos_found.get('hotelImages')):
        if num == quantity:
            break

        url = image.get('baseUrl').replace('_{size}', '')
        found_urls.append(url)

    return found_urls
