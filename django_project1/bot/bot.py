import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio
import os

TOKEN = "8319374247:AAG__sCoZGzIKwOoe-yc-bRJKFW4DKJretQ"
API_URL = "http://127.0.0.1:8000/users/"


bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------- GET ----------
@dp.message(Command("users"))
async def get_users(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as resp:
            if resp.status == 200:
                data = await resp.json()
                if not data:
                    await message.answer("👤 Список пользователей пуст.")
                    return
                text = "\n".join([f"{u['id']}. {u['name']} {u['last_name']}" for u in data])
                await message.answer(f"📋 Список пользователей:\n{text}")
            else:
                await message.answer("❌ Ошибка при получении списка пользователей.")

# ---------- POST ----------
@dp.message(Command("add"))
async def add_user(message: types.Message):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Используй формат:\n`/add имя фамилия`", parse_mode="Markdown")
        return

    name, last_name = parts[1], parts[2]

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json={"name": name, "last_name": last_name}) as resp:
            if resp.status == 201:
                data = await resp.json()
                await message.answer(f"✅ Пользователь добавлен:\nID: {data['id']}\nИмя: {data['name']} {data['last_name']}")
            else:
                await message.answer("❌ Ошибка при добавлении пользователя.")

# ---------- PUT ----------
@dp.message(Command("update"))
async def update_user(message: types.Message):
    parts = message.text.split()
    if len(parts) < 4:
        await message.answer("Используй формат:\n`/update id имя фамилия`", parse_mode="Markdown")
        return

    user_id, name, last_name = parts[1], parts[2], parts[3]

    async with aiohttp.ClientSession() as session:
        async with session.put(API_URL, json={"id": int(user_id), "name": name, "last_name": last_name}) as resp:
            if resp.status == 200:
                data = await resp.json()
                await message.answer(f"✏️ Обновлён:\n{data['id']}: {data['name']} {data['last_name']}")
            else:
                await message.answer("❌ Ошибка при обновлении пользователя.")

# ---------- DELETE ----------
@dp.message(Command("delete"))
async def delete_user(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Используй формат:\n`/delete id`", parse_mode="Markdown")
        return

    user_id = int(parts[1])

    async with aiohttp.ClientSession() as session:
        async with session.delete(API_URL, json={"id": user_id}) as resp:
            if resp.status == 200:
                await message.answer(f"🗑 Пользователь с id={user_id} удалён.")
            else:
                await message.answer("❌ Ошибка при удалении пользователя.")

# ---------- Запуск ----------
async def main():
    print("Бот запущен ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
