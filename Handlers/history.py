import logging
from aiogram import types, Dispatcher
from Database.sqlite_db import show_tables


async def cmd_history(message: types.Message):
    """
    Obtains the last 5 successful search results from the database.
    """
    logging.info(f'Getting history of user {message.from_user.id}')

    result = show_tables(message)
    await message.answer('Получаем последние 5 запросов')
    for res in result:
        await message.answer('ID пользователя: {ID}\n'
                             'Дата и время запроса: {time}\n'
                             'Команда: {command}\n'
                             'Найденные отели: {matches}'.format(ID=res[0],
                                                                 time=res[1],
                                                                 command=res[2],
                                                                 matches=res[3]))
    await message.answer('Наберите /start для начала общения с ботом.')


def register_handlers_history(dp: Dispatcher):
    dp.register_message_handler(cmd_history, commands='history')
