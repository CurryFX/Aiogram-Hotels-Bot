import requests
import logging
import json
from typing import Optional, List, Tuple, Dict
from Funcs.funcs import str_to_float

from config import API_KEY

"""
    This file includes functions for interaction with RapidAPI.
"""


def api_query(url: str, params: Dict) -> requests.Response:
    """
    Is used to replace repeated GET queries in functions
    """
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    return requests.get(url=url, params=params, headers=headers, allow_redirects=True, timeout=10)


def get_city(query: str = 'New York') -> Tuple[Optional[str], Optional[int]]:
    """
    Finds an ID of the destination city.
    """

    url = "https://hotels4.p.rapidapi.com/locations/v2/search"

    querystring = {"query": query, "locale": "ru_RU", "currency": "RUB"}

    response = api_query(url=url, params=querystring)
    if response.status_code not in range(100, 300):
        logging.warning('Query failed with status code {}'.format(response.status_code))
        return None, None

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

    hotels_found = []

    response = api_query(url=url, params=querystring)
    if response.status_code not in range(100, 300):
        logging.warning('Query failed with status code {}'.format(response.status_code))
        return hotels_found

    json_response = json.loads(response.text)

    if distance is None:
        hotels_found = json_response['data']['body']['searchResults']['results']

    else:
        for hotel in json_response['data']['body']['searchResults']['results']:
            hotel_dist = str_to_float(hotel['landmarks'][0]['distance'].split(' ')[0])
            if hotel_dist <= distance:
                hotels_found.append(hotel)

    return hotels_found


def get_photos(hotel_id: int, quantity: int = 5) -> Optional[List]:

    """
    Uses GET query to receive a list of photos urls for one particular hotel

    :param hotel_id: Hotel ID from the previous function
    :param quantity: Number of photos
    :return: List of photos urls OR None if failed
    """

    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    querystring = {"id": hotel_id}

    response = api_query(url=url, params=querystring)
    if response.status_code not in range(100, 300):
        logging.warning('Query failed with status code {}'.format(response.status_code))
        return None

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
