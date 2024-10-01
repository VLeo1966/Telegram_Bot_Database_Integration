import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from config import TOKEN, TOKEN2

import random

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command('photo'))
async def photo(message: Message):
        list = ['https://avatars.mds.yandex.net/i?id=1cf04a6f38f0be15415a0c35010d27a3c5e70e21-4318341-images-thumbs&n=13',
                'https://avatars.mds.yandex.net/i?id=2414e1a11e8ea018c07319af1c31604f93fa0baa-10165663-images-thumbs&n=13',
                'https://avatars.mds.yandex.net/i?id=423098ad090e0ab751f1ebeef408125a473db425-9283819-images-thumbs&n=13',
                'https://avatars.mds.yandex.net/i?id=a8ffc42530d11d373e07ff512a9e4a96a6562d79-12731000-images-thumbs&n=13']
        rand_photo = random.choice(list)
        await message.answer_photo(photo=rand_photo, caption='Это супер крутая картинка')

@dp.message(F.photo)
async def react_photo(message: Message):
    list = ['Ого, какая фотка!', 'Непонятно, что это такое', 'Не отправляй мне такое больше']
    rand_answ = random.choice(list)
    await message.answer(rand_answ)
@dp.message(F.text == "Что такое ИИ?")
async def aitext(message: Message):
    await message.answer('Искусственный интеллект — это свойство искусственных интеллектуальных систем выполнять творческие функции, которые традиционно считаются прерогативой человека; наука и технология создания интеллектуальных машин, особенно интеллектуальных компьютерных программ')

@dp.message(Command('help'))
async def help(message: Message):
    await message.answer("Этот бот умеет выполнять команды: \n /start \n /help \n /weather Москва")

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Приветики, я бот!")

# Определение состояний
class WeatherState(StatesGroup):
    waiting_for_city = State()

# Функция для получения погоды
def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={TOKEN2}&units=metric&lang=ru"
    response = requests.get(url)

    # Проверка на успешный запрос
    if response.status_code == 200:
        data = response.json()
        city_name = data['name']
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        return f"🏙 Город: {city_name}\n🌡 Температура: {temperature}°C\n☁ Описание: {weather_description.capitalize()}\n💧 Влажность: {humidity}%\n💨 Скорость ветра: {wind_speed} м/с"
    else:
        return "Не удалось получить данные о погоде. Проверьте название города."


# Обработчик команды /weather
@dp.message(Command("weather"))
async def weather_command(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, укажите название города.")
    await state.set_state(WeatherState.waiting_for_city)  # Устанавливаем состояние ожидания города

# Обработчик ввода названия города
@dp.message(WeatherState.waiting_for_city)
async def process_city_input(message: Message, state: FSMContext):
    city = message.text
    weather_info = get_weather(city)
    await message.answer(weather_info)
    await state.clear()  # Сбрасываем состояние после получения прогноза


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())