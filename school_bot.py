import sqlite3
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Определяем состояния для машины состояний
class Form(StatesGroup):
    name = State()  # Состояние для имени
    age = State()  # Состояние для возраста
    grade = State()  # Состояние для класса

# Команда для начала ввода данных
@dp.message(Command(commands=["start"]))
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Введи своё имя.")
    await state.set_state(Form.name)

# Получаем имя пользователя
@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)

# Получаем возраст пользователя
@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        await state.update_data(age=age)
        await message.answer("В каком ты классе?")
        await state.set_state(Form.grade)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный возраст (число).")

# Получаем класс пользователя и сохраняем данные в базу
@dp.message(Form.grade)
async def process_grade(message: Message, state: FSMContext):
    await state.update_data(grade=message.text)

    # Получаем все данные
    user_data = await state.get_data()
    name = user_data['name']
    age = user_data['age']
    grade = user_data['grade']

    # Подключаемся к базе данных и сохраняем данные
    try:
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (name, age, grade) VALUES (?, ?, ?)", (name, age, grade))
        conn.commit()
        conn.close()
        await message.answer(f"Данные сохранены: Имя: {name}, Возраст: {age}, Класс: {grade}")
    except sqlite3.Error as e:
        await message.answer("Ошибка при сохранении данных в базу.")
        logging.error(f"Ошибка базы данных: {e}")

    # Сбрасываем состояние
    await state.clear()

# Функция для запуска бота
async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

# Запуск бота
if __name__ == '__main__':
    asyncio.run(main())
