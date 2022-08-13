import logging
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text


async def cmd_start(message: types.Message):
    markup = types.ReplyKeyboardRemove()
    await message.answer('Выберите команду: '
                         '\n/lowprice - поиск самых дешевых отелей '
                         '\n/highprice - поиск самых дорогих отелей'
                         '\n/bestdeal - ваш лучший выбор'
                         '\n/history - история поиска отелей'
                         '\nДля отмены поиска напишите "отмена"', reply_markup=markup)


async def not_implemented(message: types.Message):
    """
    Used to cover unfinished functionality
    """
    await message.reply('Эта команда еще в разработке. Воспользуйтесь /start для запуска бота')


async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Состояние сброшено %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Команда отменена', reply_markup=types.ReplyKeyboardRemove())
    await message.answer('Наберите /start для начала общения с ботом.')


async def greetings(message: types.Message):
    await message.answer('И тебе привет, {}'.format(message.from_user.first_name))


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=['start', 'help'])
    # dp.register_message_handler(not_implemented, commands='history')
    dp.register_message_handler(greetings, Text(equals='привет', ignore_case=True))
    dp.register_message_handler(cancel_handler, state='*', commands='отмена')
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), state='*')
