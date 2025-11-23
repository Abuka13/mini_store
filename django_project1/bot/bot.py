import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

TOKEN = "8319374247:AAG__sCoZGzIKwOoe-yc-bRJKFW4DKJretQ"
API_URL = "http://127.0.0.1:8000/api"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Хранилище сессий пользователей (теперь с токенами)
user_sessions = {}


# States для создания/обновления
class CreateUser(StatesGroup):
    username = State()
    password = State()
    first_name = State()
    last_name = State()
    email = State()
    role = State()


class CreateProduct(StatesGroup):
    name = State()
    description = State()
    category = State()
    price = State()


class UpdateUser(StatesGroup):
    user_id = State()
    username = State()
    password = State()
    first_name = State()
    last_name = State()
    email = State()
    role = State()


class UpdateProduct(StatesGroup):
    product_id = State()
    name = State()
    description = State()
    category = State()
    price = State()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def is_authenticated(telegram_user_id):
    return telegram_user_id in user_sessions


def get_role(telegram_user_id):
    return user_sessions.get(telegram_user_id, {}).get("role", None)


def get_token(telegram_user_id):
    """Получаем токен пользователя"""
    return user_sessions.get(telegram_user_id, {}).get("token", None)


def get_auth_headers(telegram_user_id):
    """Формируем headers с токеном для запросов"""
    token = get_token(telegram_user_id)
    if token:
        return {"Authorization": f"Token {token}"}
    return {}


def get_help_message(role):
    if role == "superadmin":
        return """📋 **Доступные команды для роли: superadmin**

👥 **Команды суперадминистратора:**
/users/post - Создать нового пользователя
/users/get - Показать список всех пользователей
/users/get <id> - Показать информацию о пользователе
/users/put <id> - Обновить данные пользователя
/users/delete <id> - Удалить пользователя

🛍️ **Товары:**
/products/get - Список всех товаров
/products/get <id> - Информация о товаре
/products/post - Создать новый товар
/products/put <id> - Обновить товар
/products/delete <id> - Удалить товар

🛒 **Корзина:**
/carts/add <id> [количество] - Добавить товар в корзину
/cart/get - Моя корзина

ℹ️ **Общие команды:**
/help - Показать это сообщение
/logout - Выйти из системы

📝 **Примеры:**
/users/get 1
/products/get 1"""

    elif role == "admin":
        return """📋 **Доступные команды для роли: admin**

🛍️ **Команды администратора:**
/products/get - Список всех товаров
/products/get <id> - Информация о товаре
/products/post - Создать новый товар
/products/put <id> - Обновить товар
/products/delete <id> - Удалить товар

🛒 **Корзина:**
/carts/add <id> [количество] - Добавить товар в корзину
/cart/get - Моя корзина

ℹ️ **Общие команды:**
/help - Показать это сообщение
/logout - Выйти из системы

📝 **Примеры:**
/products/get
/products/get 1"""

    else:  # user
        return """📋 **Доступные команды для роли: user**

👤 **Команды для пользователей:**
/products/get - Список всех товаров
/products/get <id> - Информация о товаре
/carts/add <id> [количество] - Добавить товар в корзину
/cart/get - Моя корзина

ℹ️ **Общие команды:**
/help - Показать это сообщение
/logout - Выйти из системы

📝 **Примеры:**
/products/get 1
/carts/add 1 2
/cart/get"""


# ========== АВТОРИЗАЦИЯ ==========
@dp.message(CommandStart())
async def start(message: types.Message):
    telegram_user_id = message.from_user.id

    if is_authenticated(telegram_user_id):
        role = get_role(telegram_user_id)
        await message.answer(f"Вы уже авторизованы как {role}.\nИспользуйте /help для списка команд.")
        return

    await message.answer(
        "Привет! Для входа в систему, введи логин и пароль через пробел\n"
        "Пример: username password"
    )


@dp.message(lambda msg: not is_authenticated(msg.from_user.id) and not msg.text.startswith('/'))
async def login(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("❌ Неверный формат. Используй: username password")
        return

    username, password = parts

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/login/", json={
            "username": username,
            "password": password
        }) as resp:
            if resp.status == 200:
                data = await resp.json()
                telegram_user_id = message.from_user.id

                # 🔥 СОХРАНЯЕМ ТОКЕН
                user_sessions[telegram_user_id] = {
                    "user_id": data["user_id"],
                    "role": data["role"],
                    "username": username,
                    "token": data["token"]  # 🔥 ТОКЕН
                }

                await message.answer(
                    f"✅ Добро пожаловать, {username}! Вы успешно вошли в систему как {data['role']}."
                )
                await message.answer(get_help_message(data['role']), parse_mode="Markdown")
            else:
                await message.answer("❌ Неверный логин или пароль.")


@dp.message(Command("logout"))
async def logout(message: types.Message):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    username = user_sessions[telegram_user_id]["username"]

    # 🔥 ОТПРАВЛЯЕМ ТОКЕН ПРИ LOGOUT
    async with aiohttp.ClientSession() as session:
        headers = get_auth_headers(telegram_user_id)
        await session.post(f"{API_URL}/logout/", headers=headers)

    del user_sessions[telegram_user_id]
    await message.answer(f"✅ {username}, вы вышли из системы. Используйте /start для входа.")


@dp.message(Command("help"))
async def help_command(message: types.Message):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    role = get_role(telegram_user_id)
    await message.answer(get_help_message(role), parse_mode="Markdown")


# ========== ПОЛЬЗОВАТЕЛИ (только superadmin) ==========
@dp.message(Command("users/get"))
async def users_get(message: types.Message):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    if get_role(telegram_user_id) != "superadmin":
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    parts = message.text.split()
    headers = get_auth_headers(telegram_user_id)  # 🔥 ДОБАВЛЯЕМ ТОКЕН

    # Если есть ID - получаем конкретного пользователя
    if len(parts) >= 2:
        user_id = parts[1]
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/users/get/{user_id}/", headers=headers) as resp:
                if resp.status == 200:
                    user = await resp.json()
                    text = f"""👤 **Информация о пользователе:**

**ID:** {user['id']}
**Username:** {user['username']}
**Имя:** {user['first_name']}
**Фамилия:** {user['last_name']}
**Email:** {user['email']}
**Роль:** {user['role']}"""
                    await message.answer(text, parse_mode="Markdown")
                else:
                    await message.answer("❌ Пользователь не найден.")
        return

    # Иначе получаем список всех пользователей
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/users/get/", headers=headers) as resp:
            if resp.status == 200:
                users = await resp.json()
                if not users:
                    await message.answer("👤 Список пользователей пуст.")
                    return

                text = "📋 **Список пользователей:**\n\n"
                for u in users:
                    text += f"**ID:** {u['id']}\n"
                    text += f"**Username:** {u['username']}\n"
                    text += f"**Имя:** {u['first_name']} {u['last_name']}\n"
                    text += f"**Роль:** {u['role']}\n\n"

                await message.answer(text, parse_mode="Markdown")
            else:
                await message.answer("❌ Ошибка при получении списка пользователей.")


@dp.message(Command("users/post"))
async def users_post_start(message: types.Message, state: FSMContext):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    if get_role(telegram_user_id) != "superadmin":
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    await message.answer("Введите username:")
    await state.set_state(CreateUser.username)


@dp.message(CreateUser.username)
async def create_user_username(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer("Введите password:")
    await state.set_state(CreateUser.password)


@dp.message(CreateUser.password)
async def create_user_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.answer("Введите имя:")
    await state.set_state(CreateUser.first_name)


@dp.message(CreateUser.first_name)
async def create_user_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Введите фамилию:")
    await state.set_state(CreateUser.last_name)


@dp.message(CreateUser.last_name)
async def create_user_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.answer("Введите email:")
    await state.set_state(CreateUser.email)


@dp.message(CreateUser.email)
async def create_user_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Введите роль (superadmin/admin/user):")
    await state.set_state(CreateUser.role)


@dp.message(CreateUser.role)
async def create_user_role(message: types.Message, state: FSMContext):
    telegram_user_id = message.from_user.id
    role = message.text

    if role not in ["superadmin", "admin", "user"]:
        await message.answer("❌ Неверная роль. Используйте: superadmin, admin или user")
        return

    data = await state.get_data()
    headers = get_auth_headers(telegram_user_id)  # 🔥 ТОКЕН

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/users/post/",
                                json={
                                    "username": data["username"],
                                    "password": data["password"],
                                    "first_name": data["first_name"],
                                    "last_name": data["last_name"],
                                    "email": data["email"],
                                    "role": role
                                },
                                headers=headers) as resp:
            if resp.status == 201:
                user = await resp.json()
                await message.answer(
                    f"✅ Пользователь создан!\nID: {user['id']}\nUsername: {user['username']}\nРоль: {user['role']}")
            else:
                await message.answer("❌ Ошибка при создании пользователя.")

    await state.clear()


@dp.message(Command("users/put"))
async def users_put_start(message: types.Message, state: FSMContext):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    if get_role(telegram_user_id) != "superadmin":
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Используй формат: `/users/put <id>`", parse_mode="Markdown")
        return

    user_id = parts[1]
    await state.update_data(user_id=user_id)
    await message.answer("Введите новый username (или '-' чтобы оставить прежним):")
    await state.set_state(UpdateUser.username)


@dp.message(UpdateUser.username)
async def update_user_username(message: types.Message, state: FSMContext):
    username = message.text if message.text != '-' else None
    await state.update_data(username=username)
    await message.answer("Введите новый password (или '-' чтобы оставить прежним):")
    await state.set_state(UpdateUser.password)


@dp.message(UpdateUser.password)
async def update_user_password(message: types.Message, state: FSMContext):
    password = message.text if message.text != '-' else None
    await state.update_data(password=password)
    await message.answer("Введите новое имя (или '-' чтобы оставить прежним):")
    await state.set_state(UpdateUser.first_name)


@dp.message(UpdateUser.first_name)
async def update_user_first_name(message: types.Message, state: FSMContext):
    first_name = message.text if message.text != '-' else None
    await state.update_data(first_name=first_name)
    await message.answer("Введите новую фамилию (или '-' чтобы оставить прежней):")
    await state.set_state(UpdateUser.last_name)


@dp.message(UpdateUser.last_name)
async def update_user_last_name(message: types.Message, state: FSMContext):
    last_name = message.text if message.text != '-' else None
    await state.update_data(last_name=last_name)
    await message.answer("Введите новый email (или '-' чтобы оставить прежним):")
    await state.set_state(UpdateUser.email)


@dp.message(UpdateUser.email)
async def update_user_email(message: types.Message, state: FSMContext):
    email = message.text if message.text != '-' else None
    await state.update_data(email=email)
    await message.answer("Введите новую роль (superadmin/admin/user или '-' чтобы оставить прежней):")
    await state.set_state(UpdateUser.role)


@dp.message(UpdateUser.role)
async def update_user_role(message: types.Message, state: FSMContext):
    telegram_user_id = message.from_user.id
    role = message.text if message.text != '-' else None

    if role and role not in ["superadmin", "admin", "user"]:
        await message.answer("❌ Неверная роль. Используйте: superadmin, admin, user или '-'")
        return

    data = await state.get_data()
    user_id = data["user_id"]

    # Формируем JSON только с непустыми полями
    update_data = {}
    if data.get("username"):
        update_data["username"] = data["username"]
    if data.get("password"):
        update_data["password"] = data["password"]
    if data.get("first_name"):
        update_data["first_name"] = data["first_name"]
    if data.get("last_name"):
        update_data["last_name"] = data["last_name"]
    if data.get("email"):
        update_data["email"] = data["email"]
    if role:
        update_data["role"] = role

    headers = get_auth_headers(telegram_user_id)  # 🔥 ТОКЕН

    async with aiohttp.ClientSession() as session:
        async with session.put(f"{API_URL}/users/put/{user_id}/",
                               json=update_data,
                               headers=headers) as resp:
            if resp.status == 200:
                user = await resp.json()
                await message.answer(
                    f"✅ Пользователь обновлен!\nID: {user['id']}\nUsername: {user['username']}\nРоль: {user['role']}")
            else:
                await message.answer("❌ Ошибка при обновлении пользователя.")

    await state.clear()


@dp.message(Command("users/delete"))
async def users_delete(message: types.Message):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    if get_role(telegram_user_id) != "superadmin":
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Используй формат: `/users/delete <id>`", parse_mode="Markdown")
        return

    user_id = parts[1]
    headers = get_auth_headers(telegram_user_id)  # 🔥 ТОКЕН

    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_URL}/users/delete/{user_id}/", headers=headers) as resp:
            if resp.status == 200:
                await message.answer(f"🗑 Пользователь с ID={user_id} удалён.")
            else:
                await message.answer("❌ Ошибка при удалении пользователя.")


# ========== ТОВАРЫ ==========
@dp.message(Command("products/get"))
async def products_get(message: types.Message):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    parts = message.text.split()
    headers = get_auth_headers(telegram_user_id)  # 🔥 ТОКЕН

    # Если есть ID - получаем конкретный товар
    if len(parts) >= 2:
        product_id = parts[1]
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/products/get/{product_id}/", headers=headers) as resp:
                if resp.status == 200:
                    product = await resp.json()
                    text = f"""🛍️ **Информация о товаре:**

**ID:** {product['id']}
**Название:** {product['name']}
**Описание:** {product['description']}
**Цена:** {product['price']} ₸
**Категория:** {product['category']}"""
                    await message.answer(text, parse_mode="Markdown")
                else:
                    await message.answer("❌ Товар не найден.")
        return

    # Иначе получаем список всех товаров
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/products/get/", headers=headers) as resp:
            if resp.status == 200:
                products = await resp.json()
                if not products:
                    await message.answer("🛍️ Список товаров пуст.")
                    return

                text = "🛍️ **Список товаров:**\n\n"
                for p in products:
                    text += f"**ID:** {p['id']}\n"
                    text += f"**Название:** {p['name']}\n"
                    text += f"**Цена:** {p['price']} ₸\n"
                    text += f"**Категория:** {p['category']}\n\n"

                await message.answer(text, parse_mode="Markdown")
            else:
                await message.answer("❌ Ошибка при получении списка товаров.")


@dp.message(Command("products/post"))
async def products_post_start(message: types.Message, state: FSMContext):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    role = get_role(telegram_user_id)
    if role not in ["admin", "superadmin"]:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    await message.answer("Введите название товара:")
    await state.set_state(CreateProduct.name)


@dp.message(CreateProduct.name)
async def create_product_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание:")
    await state.set_state(CreateProduct.description)


@dp.message(CreateProduct.description)
async def create_product_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите категорию (clothes/sport/home/electronics):")
    await state.set_state(CreateProduct.category)


@dp.message(CreateProduct.category)
async def create_product_category(message: types.Message, state: FSMContext):
    category = message.text
    if category not in ["clothes", "sport", "home", "electronics"]:
        await message.answer("❌ Неверная категория. Используйте: clothes, sport, home, electronics")
        return

    await state.update_data(category=category)
    await message.answer("Введите цену:")
    await state.set_state(CreateProduct.price)


@dp.message(CreateProduct.price)
async def create_product_price(message: types.Message, state: FSMContext):
    telegram_user_id = message.from_user.id

    try:
        price = float(message.text)
    except ValueError:
        await message.answer("❌ Неверный формат цены. Введите число.")
        return

    data = await state.get_data()
    headers = get_auth_headers(telegram_user_id)  # 🔥 ТОКЕН

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/products/post/",
                                json={
                                    "name": data["name"],
                                    "description": data["description"],
                                    "category": data["category"],
                                    "price": price
                                },
                                headers=headers) as resp:
            if resp.status == 201:
                product = await resp.json()
                await message.answer(
                    f"✅ Товар создан!\nID: {product['id']}\nНазвание: {product['name']}\nЦена: {product['price']} ₸")
            else:
                await message.answer("❌ Ошибка при создании товара.")

    await state.clear()


@dp.message(Command("products/put"))
async def products_put_start(message: types.Message, state: FSMContext):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    role = get_role(telegram_user_id)
    if role not in ["admin", "superadmin"]:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Используй формат: `/products/put <id>`", parse_mode="Markdown")
        return

    product_id = parts[1]
    await state.update_data(product_id=product_id)
    await message.answer("Введите новое название (или '-' чтобы оставить прежним):")
    await state.set_state(UpdateProduct.name)


@dp.message(UpdateProduct.name)
async def update_product_name(message: types.Message, state: FSMContext):
    name = message.text if message.text != '-' else None
    await state.update_data(name=name)
    await message.answer("Введите новое описание (или '-' чтобы оставить прежним):")
    await state.set_state(UpdateProduct.description)


@dp.message(UpdateProduct.description)
async def update_product_description(message: types.Message, state: FSMContext):
    description = message.text if message.text != '-' else None
    await state.update_data(description=description)
    await message.answer("Введите новую категорию (clothes/sport/home/electronics или '-'):")
    await state.set_state(UpdateProduct.category)


@dp.message(UpdateProduct.category)
async def update_product_category(message: types.Message, state: FSMContext):
    category = message.text if message.text != '-' else None
    if category and category not in ["clothes", "sport", "home", "electronics"]:
        await message.answer("❌ Неверная категория. Используйте: clothes, sport, home, electronics или '-'")
        return

    await state.update_data(category=category)
    await message.answer("Введите новую цену (или '-' чтобы оставить прежней):")
    await state.set_state(UpdateProduct.price)


@dp.message(UpdateProduct.price)
async def update_product_price(message: types.Message, state: FSMContext):
    telegram_user_id = message.from_user.id
    price_text = message.text
    price = None

    if price_text != '-':
        try:
            price = float(price_text)
        except ValueError:
            await message.answer("❌ Неверный формат цены. Введите число или '-'.")
            return

    data = await state.get_data()
    product_id = data["product_id"]

    # Формируем JSON только с непустыми полями
    update_data = {}
    if data.get("name"):
        update_data["name"] = data["name"]
    if data.get("description"):
        update_data["description"] = data["description"]
    if data.get("category"):
        update_data["category"] = data["category"]
    if price is not None:
        update_data["price"] = price

    headers = get_auth_headers(telegram_user_id)  # 🔥 ТОКЕН

    async with aiohttp.ClientSession() as session:
        async with session.put(f"{API_URL}/products/put/{product_id}/",
                               json=update_data,
                               headers=headers) as resp:
            if resp.status == 200:
                product = await resp.json()
                await message.answer(
                    f"✅ Товар обновлен!\nID: {product['id']}\nНазвание: {product['name']}\nЦена: {product['price']} ₸")
            else:
                await message.answer("❌ Ошибка при обновлении товара.")

    await state.clear()


@dp.message(Command("products/delete"))
async def products_delete(message: types.Message):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    role = get_role(telegram_user_id)
    if role not in ["admin", "superadmin"]:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Используй формат: `/products/delete <id>`", parse_mode="Markdown")
        return

    product_id = parts[1]
    headers = get_auth_headers(telegram_user_id)  # 🔥 ТОКЕН

    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_URL}/products/delete/{product_id}/", headers=headers) as resp:
            if resp.status == 200:
                await message.answer(f"🗑 Товар с ID={product_id} удалён.")
            else:
                await message.answer("❌ Ошибка при удалении товара.")


# ========== КОРЗИНА ==========
@dp.message(Command("carts/add"))
async def carts_add(message: types.Message):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Используй формат: `/carts/add <id> [количество]`", parse_mode="Markdown")
        return

    product_id = parts[1]
    quantity = int(parts[2]) if len(parts) > 2 else 1
    headers = get_auth_headers(telegram_user_id)  # 🔥 ТОКЕН

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/carts/add/{product_id}/",
                                json={"quantity": quantity},
                                headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                await message.answer(f"✅ {data['message']}\nВсего в корзине: {data.get('quantity', quantity)} шт.")
            else:
                await message.answer("❌ Ошибка при добавлении товара в корзину.")


@dp.message(Command("cart/get"))
async def cart_get(message: types.Message):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")
        return

    headers = get_auth_headers(telegram_user_id)  # 🔥 ТОКЕН

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/cart/", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()

                if not data["items"]:
                    await message.answer("🛒 Ваша корзина пуста.")
                    return

                text = "🛒 **Ваша корзина:**\n\n"
                for item in data["items"]:
                    item_price = float(item['price'])
                    item_quantity = item['quantity']
                    item_total = item_price * item_quantity

                    text += (
                        f"**{item['product_name']}**\n"
                        f"Цена за 1 шт: {item_price} ₸\n"
                        f"Количество: {item_quantity} шт.\n"
                        f"Итого: {item_total} ₸\n\n"
                    )

                text += f"💰 **Общая сумма: {data['total']} ₸**"

                await message.answer(text, parse_mode="Markdown")
            else:
                await message.answer("❌ Ошибка при получении корзины.")


@dp.message()
async def unauthorized_command(message: types.Message):
    telegram_user_id = message.from_user.id

    if not is_authenticated(telegram_user_id):
        await message.answer("🔐 Используйте /start для входа в систему.")


# ========== ЗАПУСК ==========
async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())