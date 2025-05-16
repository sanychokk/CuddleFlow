from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

import os
import asyncio
import aiosqlite
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import db  # твой db.py
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("BOT_TOKEN")
print(token)
bot = Bot(token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Определяем состояния для FSM
class Form(StatesGroup):
    waiting_for_cycle = State()
    waiting_for_cravings = State()

@dp.message(Command("start"))
async def start(msg: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Я девушка", callback_data="role_girl")
    kb.button(text="Я парень", callback_data="role_boy")
    await msg.answer("Привет! Кто ты?", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("role_"))
async def choose_role(callback: types.CallbackQuery):
    role = callback.data.split("_")[1]
    user_id = callback.from_user.id
    name = callback.from_user.full_name

    await db.create_user(user_id, role, name)

    if role == "girl":
        await callback.message.answer(
            "Ты выбрала роль: девушка 🌸\nТеперь можешь использовать /panel"
        )
    else:
        await callback.message.answer(
            "Ты выбрал роль: парень 🧸\nТы будешь получать уведомления и список вкусняшек."
        )
    await callback.answer()

@dp.message(Command("panel"))
async def show_panel(msg: types.Message):
    user_id = msg.from_user.id
    role = await db.get_user_role(user_id)

    kb = InlineKeyboardBuilder()

    if role == "girl":
        kb.button(text="🔴 Начались месячные", callback_data="start_period")
        kb.button(text="📅 Посмотреть календарь", callback_data="show_calendar")
        kb.button(text="⚙️ Настроить цикл", callback_data="set_cycle")
        kb.button(text="🔗 Сгенерировать код для парня", callback_data="gen_code")
        await msg.answer("Панель управления:", reply_markup=kb.as_markup())

    elif role == "boy":
        kb.button(text="🍬 Посмотреть список вкусняшек", callback_data="get_cravings")
        await msg.answer("Панель парня:", reply_markup=kb.as_markup())

    else:
        await msg.answer("Ты не выбрал роль. Напиши /start")

# --- FSM для установки цикла ---
@dp.callback_query(F.data == "set_cycle")
async def set_cycle(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи длительность цикла (например, 28):")
    await state.set_state(Form.waiting_for_cycle)
    await callback.answer()

@dp.message(Form.waiting_for_cycle)
async def save_cycle_length(msg: types.Message, state: FSMContext):
    try:
        days = int(msg.text.strip())
        if 20 <= days <= 45:
            await db.set_cycle_length(msg.from_user.id, days)
            await msg.answer(f"✅ Цикл установлен: {days} дней.")
            await state.clear()
        else:
            await msg.answer("Пожалуйста, введи число от 20 до 45.")
    except:
        await msg.answer("Нужно ввести число, например: 28")

# --- FSM для начала периода и ввода вкусняшек ---
@dp.callback_query(F.data == "start_period")
async def start_period(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")
    await db.set_last_period_date(user_id, today)
    await callback.message.answer("Записала! А теперь напиши, что ты хочешь:")
    await state.set_state(Form.waiting_for_cravings)
    await callback.answer()

@dp.message(Form.waiting_for_cravings)
async def save_cravings(msg: types.Message, state: FSMContext):
    text = msg.text.strip()
    await db.set_cravings(msg.from_user.id, text)
    await msg.answer("Записала 🍫💐")
    await state.clear()

    # Отправляем уведомление парню с кнопкой оплаты
    async with aiosqlite.connect(db.DB_NAME) as conn:
        cursor = await conn.execute("SELECT partner_id FROM users WHERE tg_id = ?", (msg.from_user.id,))
        row = await cursor.fetchone()

    if row and row[0]:
        partner_id = row[0]
        kb = InlineKeyboardBuilder()
        kb.button(text="💳 Обязуюсь купить вкусняшки своей любимой", callback_data="confirm_payment")

        await bot.send_message(
            partner_id,
            f"🍬 Ей хочется: {text}\n\nНажми кнопку ниже, если обязуешься купить вкусняшки.",
            reply_markup=kb.as_markup()
        )

@dp.callback_query(F.data == "confirm_payment")
async def confirm_payment(callback: types.CallbackQuery):
    payer_id = callback.from_user.id  # парень
    async with aiosqlite.connect(db.DB_NAME) as conn:
        cursor = await conn.execute("SELECT partner_id FROM users WHERE tg_id = ?", (payer_id,))
        row = await cursor.fetchone()

    if row and row[0]:
        girl_id = row[0]
        # Парню — ответ в чат
        await callback.message.answer("Спасибо за заботу! 💖")
        # Девушке — уведомление об обязательстве оплатить
        await bot.send_message(girl_id, "Обязуюсь купить вкусняшки не позднее трёх дней 💪")

    await callback.answer()

@dp.callback_query(F.data == "show_calendar")
async def show_calendar_callback(callback: types.CallbackQuery):
    await show_calendar(callback.message)
    await callback.answer()

@dp.message(Command("calendar"))
async def show_calendar(msg: types.Message):
    user_id = msg.from_user.id
    async with aiosqlite.connect(db.DB_NAME) as conn:
        cursor = await conn.execute("SELECT last_period_date FROM users WHERE tg_id = ?", (user_id,))
        row = await cursor.fetchone()

    if not row or not row[0]:
        await msg.answer("Нет данных о последнем цикле. Нажми «🔴 Начались месячные» в /panel.")
        return

    last_date = datetime.strptime(row[0], "%Y-%m-%d")
    cycle_days = await db.get_cycle_length(user_id)
    period_days = 5

    period_dates = [last_date + timedelta(days=i) for i in range(period_days)]
    next_start = last_date + timedelta(days=cycle_days)
    next_period = [next_start + timedelta(days=i) for i in range(period_days)]

    days = [last_date + timedelta(days=i) for i in range(35)]
    colors = []

    for day in days:
        if day in period_dates:
            colors.append("red")
        elif day in next_period:
            colors.append("pink")
        else:
            colors.append("lightgray")

    fig, ax = plt.subplots(figsize=(10, 1))
    ax.barh(["Цикл"], [1]*len(days), left=range(len(days)), color=colors)
    ax.set_yticks([])
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels([d.strftime("%d.%m") for d in days], rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    await msg.answer_photo(photo=buf, caption="📅 Твой календарь: красное — сейчас, розовое — следующее")

@dp.callback_query(F.data == "get_cravings")
async def get_cravings(callback: types.CallbackQuery):
    text = await db.get_cravings(callback.from_user.id)
    if text:
        await callback.message.answer(f"🍬 Ей хочется: {text}")
    else:
        await callback.message.answer("Пока нет списка вкусняшек 😢")
    await callback.answer()

@dp.callback_query(F.data == "gen_code")
async def generate_code(callback: types.CallbackQuery):
    code = await db.generate_invite_code(callback.from_user.id)
    await callback.message.answer(
        f"🔗 Твой код: `{code}`\nОтправь его своему парню — пусть введёт команду:\n\n`/connect {code}`",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(Command("connect"))
async def connect_partner(msg: types.Message):
    args = msg.text.split()
    if len(args) != 2:
        await msg.answer("Использование: /connect КОД")
        return

    code = args[1].strip().upper()
    success = await db.connect_users_by_code(code, msg.from_user.id)

    if success:
        await msg.answer("✅ Связь установлена! Теперь ты будешь получать уведомления и вкусняшки.")
    else:
        await msg.answer("❌ Код не найден. Проверь правильность.")

async def reminder_loop():
    while True:
        girls = await db.get_reminder_targets()
        for girl_id, partner_id, name in girls:
            try:
                await bot.send_message(
                    partner_id,
                    f"📅 Похоже, у {name or 'твоей девушки'} скоро снова начнутся месячные.\nПоддержи её 💖"
                )
                await db.set_last_period_date(girl_id, None)
            except Exception as e:
                print(f"Ошибка при уведомлении: {e}")
        await asyncio.sleep(86400)  # раз в сутки

async def main():
    await db.init_db()
    asyncio.create_task(reminder_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
