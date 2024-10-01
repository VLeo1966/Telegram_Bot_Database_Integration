import asyncio
import logging
import aiohttp
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN, WEATHER_API_KEY

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Класс состояний пользователя
class Form(StatesGroup):
    name = State()
    age = State()
    city = State()

# Функция инициализации базы данных
def init_db():
    conn = sqlite3.connect('user_data.db')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        city TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Команда /start
@dp.message(Command(commands=['start']))
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Как тебя зовут?")
    await state.set_state(Form.name)

# Получение имени пользователя
@dp.message(Form.name)
async def name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)

# Получение возраста пользователя
@dp.message(Form.age)
async def age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if age < 0:
            raise ValueError
        await state.update_data(age=age)
        await message.answer("Из какого ты города?")
        await state.set_state(Form.city)
    except ValueError:
        await message.answer("Пожалуйста, введи корректный возраст (целое число).")

# Получение города пользователя и запрос погоды
@dp.message(Form.city)
async def city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    user_data = await state.get_data()

    # Сохранение данных пользователя в базу данных
    try:
        conn = sqlite3.connect('user_data.db')
        cur = conn.cursor()
        cur.execute('INSERT INTO users (name, age, city) VALUES (?, ?, ?)',
                    (user_data['name'], user_data['age'], user_data['city']))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Ошибка при работе с базой данных: {e}")
        await message.answer("Произошла ошибка при сохранении данных.")
        return

    # Получение данных о погоде
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://api.openweathermap.org/data/2.5/weather?q={user_data['city']}&appid={WEATHER_API_KEY}&units=metric&lang=ru",
                    timeout=10) as response:

                if response.status == 200:
                    weather_data = await response.json()
                    main = weather_data['main']
                    weather = weather_data['weather'][0]
                    temperature = main['temp']
                    humidity = main['humidity']
                    wind_speed = weather_data['wind']['speed']

                    description = weather['description']
                    weather_report = (f"🏙 Город: {user_data['city']}\n"
                                      f"🌡 Температура: {temperature}°C\n"
                                      f"☁ Описание: {description}\n"
                                      f"💧 Влажность: {humidity}%\n"
                                      f"💨 Скорость ветра: {wind_speed} м/с")
                    await message.answer(weather_report)
                else:
                    await message.answer("Не удалось получить данные о погоде.")
    except aiohttp.ClientConnectorError:
        await message.answer("Ошибка соединения с сервером погоды. Проверьте подключение к интернету.")
    except asyncio.TimeoutError:
        await message.answer("Превышено время ожидания ответа от сервера погоды.")
    except Exception as e:
        logging.error(f"Ошибка при запросе погоды: {e}")
        await message.answer("Произошла непредвиденная ошибка при запросе погоды.")

    # Очистка состояния
    await state.clear()


# Инициализация базы данных перед запуском
init_db()


# Основная функция для запуска бота
async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


# Запуск бота
if __name__ == '__main__':
    asyncio.run(main())
