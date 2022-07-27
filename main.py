import logging
from config import dp, bot
from aiogram.utils import executor
from Database.sqlite_db import create_database
from Handlers import hi_lo_price, common, bestdeal, history


if __name__ == '__main__':
    common.register_handlers_common(dp)
    hi_lo_price.register_handlers_hi_lo_price(dp)
    bestdeal.register_handlers_bestdeal(dp)
    history.register_handlers_history(dp)

    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True, on_startup=create_database())
