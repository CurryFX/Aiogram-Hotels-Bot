import logging
from datetime import datetime, date, timedelta
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from State.user_state import HotelRequest
from Funcs import rapid_api
from Database.sqlite_db import add_row
from config import bot


async def get_cmd(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['command'] = message.text

    await HotelRequest.next()
    await message.answer('Итак, в какой город едем?')


async def get_city(message: types.Message, state: FSMContext):
    """
    Finds and uses the first result of query. Doesn't specify the query result.
    """
    city_name, city_id = rapid_api.get_city(message.text)
    logging.info(f'User city request: {message.text}')
    logging.info(f'Found city name: {city_name} ID: {city_id}')
    if city_id is None:
        await message.answer('Город не найден. Можете попробовать снова')
        return
    else:
        await message.answer(f'{city_name} - хороший город')

    await state.update_data(city_name=city_name, city_id=city_id)
    await HotelRequest.next()

    calendar, step = DetailedTelegramCalendar(calendar_id=1, min_date=date.today()).build()
    await bot.send_message(message.chat.id,
                           f"Когда приезжаете? Выберите дату",
                           reply_markup=calendar)


async def arrival(query: types.CallbackQuery, state: FSMContext):
    """
    Callback with a calendar for arrival date. Makes sure the date cannot be earlier than today.
    """
    result, key, step = DetailedTelegramCalendar(calendar_id=1, locale='ru',
                                                 min_date=date.today()).process(query.data)

    if not result and key:
        await bot.edit_message_text(f"Select {LSTEP[step]}",
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=key)
    elif result:
        await bot.edit_message_text(f"Приезжаете {result}",
                                    query.message.chat.id,
                                    query.message.message_id)

        await state.update_data(check_in=result)
        calendar, step = DetailedTelegramCalendar(calendar_id=2, locale='ru',
                                                  min_date=(result+timedelta(1))).build()
        await bot.send_message(query.message.chat.id,
                               f"А уезжать когда? Выберите дату",
                               reply_markup=calendar)
        logging.info(f"Check in: {result}")
        await HotelRequest.next()


async def departure(query: types.CallbackQuery, state: FSMContext):
    """
    Callback with a calendar for departure date. Makes sure the date cannot be earlier than arrival date.
    """
    data = await state.get_data()

    result, key, step = DetailedTelegramCalendar(calendar_id=2, locale='ru',
                                                 min_date=data.get('check_in') + timedelta(1)).process(query.data)

    if not result and key:
        await bot.edit_message_text(f"Select {LSTEP[step]}",
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=key)
    elif result:
        await bot.edit_message_text(f"Уезжаете {result}",
                                    query.message.chat.id,
                                    query.message.message_id)

        await state.update_data(check_out=result)
        logging.info(f'Check out: {result}')
        await bot.send_message(query.message.chat.id, 'Сколько отелей показать? (1-10)')
        await HotelRequest.next()


async def hotels(message: types.Message, state: FSMContext):
    """
    Takes the amount of hotels from the message that have to be shown.
    """
    if not message.text.isdecimal():
        return await message.answer('Число должно быть целым')
    elif not (0 < int(message.text) <= 10):
        return await message.answer('Число должно быть в пределах 1-10')

    await state.update_data(hotels_num=int(message.text))
    await HotelRequest.need_photos.set()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Да", "Нет")

    await message.answer('А что по фоткам? Загружать?', reply_markup=markup)


async def need_photos_bad_answer(message: types.Message):
    """
    Incorrect 'yes or no' answer handler.
    """
    return await message.answer("Некорректный ответ. Выберите одну из кнопок")


async def need_photos(message: types.Message, state: FSMContext):
    """
    Handler for number of photos for each hotel to be shown.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add('1', '2', '3', '4', '5')

    await state.update_data(need_photos=True)
    await HotelRequest.next()
    await message.answer("Сколько фоток нужно? (1-5)", reply_markup=markup)


async def photos_num_bad_answer(message: types.Message):
    """
    Incorrect keyboard answer handler.
    """
    logging.info('Bad photos answer:', message.text)
    return await message.answer("Некорректный ответ. Выберите одну из кнопок")


async def result(message: types.Message, state: FSMContext):
    """
    Takes all the data gathered above to form the final list of the desired hotels and photos to them.
    The function is common for all the commands. Also, gathered data is moved to the database here.
    If the hotels list is empty, returns nothing
    """
    logging.info(f'Number of photos: {message.text}')
    markup = types.ReplyKeyboardRemove()
    await message.answer("Вот результат", reply_markup=markup)

    data = await state.get_data()
    if data.get('command') == '/lowprice':
        sort_order = 'PRICE'
    elif data.get('command') == '/highprice':
        sort_order = 'PRICE_HIGHEST_FIRST'
    city_id = data.get('city_id')
    quantity = data.get('hotels_num')
    check_in = data.get('check_in')
    check_out = data.get('check_out')

    hotels_found = rapid_api.get_city_hotels(city_id, quantity, check_in, check_out, sort_order)

    if len(hotels_found) == 0:
        await state.finish()
        await message.answer("По запросу отелей не найдено")
        return
    elif hotels_found is None:
        await state.finish()
        await message.answer("Что-то пошло не так. Попробуйте еще раз")
        return

    #   Заносим данные о поиске в базу данных
    user_id = message.from_user.id
    time = str(datetime.isoformat(datetime.today(), sep=' ', timespec='seconds'))
    command = str(data.get('command'))
    matches = ' | '.join([hotel['name'] if len(hotels_found) != 0 else None for hotel in hotels_found])
    add_row(user_id, time, command, matches)
    # -------------------------------------------

    await HotelRequest.next()
    await print_result(message, state, hotels_found)


async def print_result(message, state, hotels_found):
    """
    Brings gathered info about hotels to user
    """
    data = await state.get_data()
    days = (data.get('check_out') - data.get('check_in')).days

    for num, hotel in enumerate(hotels_found, start=1):
        if data.get('need_photos'):
            urls = rapid_api.get_photos(hotel['id'], int(message.text))
            await types.ChatActions.upload_photo()
            media = types.MediaGroup()

            if urls is not None:
                for url in urls:
                    media.attach_photo(url)
                await message.answer_media_group(media=media)
            else:
                await message.answer('Фотографии недоступны')

        if hotel['address'].get('streetAddress'):
            addr = ', '.join([hotel['address']['streetAddress'],
                              hotel['address']['locality'],
                              hotel['address']['region']])
        else:
            addr = ', '.join([hotel['address']['locality'],
                              hotel['address']['region']])

        await message.answer(
            '{num}) Название: {name}\n'
            'Рейтинг отеля: {rating}\n'
            'Адрес: {addr}\n'
            'Расстояние от центра: {dist}\n'
            'Цена за ночь: {price} руб.\n'
            'Цена за {days} суток: {wholePrice} руб.\n'
            'Ссылка: {link}'
            .format(num=num,
                    name=hotel['name'],
                    rating=hotel['starRating'],
                    addr=addr,
                    dist=hotel['landmarks'][0]['distance'],
                    price=hotel['ratePlan']['price']['exactCurrent'],
                    days=days,
                    wholePrice=round(days * hotel['ratePlan']['price']['exactCurrent'], 2),
                    link=f"hotels.com/ho{hotel['id']}"))
    await state.finish()
    await message.answer("Хорошего отдыха")


def register_handlers_hi_lo_price(dp: Dispatcher):
    dp.register_message_handler(get_cmd, commands=['lowprice', 'highprice'], state=None)
    dp.register_message_handler(get_city, state=HotelRequest.city)
    dp.register_callback_query_handler(arrival,
                                       DetailedTelegramCalendar.func(calendar_id=1),
                                       state=HotelRequest.check_in)
    dp.register_callback_query_handler(departure,
                                       DetailedTelegramCalendar.func(calendar_id=2),
                                       state=HotelRequest.check_out)
    dp.register_message_handler(hotels, state=HotelRequest.hotels_num)
    dp.register_message_handler(need_photos_bad_answer,
                                lambda message: message.text not in ["Да", "Нет"],
                                state=HotelRequest.need_photos)
    dp.register_message_handler(need_photos, Text(equals='Да', ignore_case=True), state=HotelRequest.need_photos)
    dp.register_message_handler(photos_num_bad_answer,
                                lambda msg: int(msg.text) not in range(1, 6),
                                state=HotelRequest.photos_num)
    dp.register_message_handler(result, Text(equals='Нет', ignore_case=True), state=HotelRequest.need_photos)
    dp.register_message_handler(result, state=HotelRequest.photos_num)
