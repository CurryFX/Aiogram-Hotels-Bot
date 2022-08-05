import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

load_dotenv()

TOKEN = os.getenv('API_TOKEN')
API_KEY = os.getenv('RAPID_API_KEY')

bot = Bot(TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
