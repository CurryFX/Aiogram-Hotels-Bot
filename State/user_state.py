from aiogram.dispatcher.filters.state import State, StatesGroup


class HotelRequest(StatesGroup):
    """
    User states for lowprice/highprice
    """
    city = State()
    check_in = State()
    check_out = State()
    hotels_num = State()
    need_photos = State()
    photos_num = State()
    result = State()
    print_result = State()


class BestDeal(StatesGroup):
    """
    User states for bestdeal
    """
    city = State()
    check_in = State()
    check_out = State()
    hotels_num = State()
    min_price = State()
    max_price = State()
    dist_from_center = State()
    need_photos = State()
    photos_num = State()
    result = State()
    print_result = State()
