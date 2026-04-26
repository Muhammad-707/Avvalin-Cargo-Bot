import os
print("BOT STARTING...")

import json
import os
import random

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
# deploy fix

from config import TOKEN, RATE_PER_KG

FILE = "data.json"


# ================= LOAD / SAVE =================
def load_users():
    if os.path.exists(FILE):
        if os.path.getsize(FILE) == 0:
            return {}
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


users = load_users()


# ================= FIX DATA =================
def fix_data():
    for u in users.values():
        for o in u.get("orders", []):
            if isinstance(o, dict):
                o.setdefault("status", "accepted")
                o.setdefault("track", "N/A")


fix_data()
save_users(users)


# ================= MENU =================
def menu():
    return ReplyKeyboardMarkup(
        [
            ["📦 Заказ", "👤 Профиль"],
            ["💰 Цена", "📋 Мои заказы"],
            ["🚚 Статус", "📍 Отследить"],
            ["🆘 Поддержка", "📞 Контакты"],
            ["ℹ О компании"]
        ],
        resize_keyboard=True
    )


MAIN_BUTTONS = {
    "📦 Заказ",
    "👤 Профиль",
    "💰 Цена",
    "📋 Мои заказы",
    "🚚 Статус",
    "📍 Отследить",
    "🆘 Поддержка",
    "📞 Контакты",
    "ℹ О компании",
}


# ================= TRACK =================
def make_track():
    return f"AV{random.randint(100000,999999)}"


# ================= STATUS =================
def pretty_status(status):
    return {
        "accepted": "📥 Принят на складе",
        "warehouse": "🏭 В обработке",
        "shipping": "🚚 В пути",
        "arrived": "📍 В стране",
        "delivered": "✅ Доставлен"
    }.get(status, "📦 Обрабатывается")


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    if uid not in users:
        users[uid] = {
            "name": "",
            "phone": "",
            "orders": []
        }
        save_users(users)

        context.user_data["step"] = "name"

        await update.message.reply_text(
            "👤 Введите ваше имя:",
            reply_markup=menu()
        )
        return

    name = users[uid].get("name", "")

    await update.message.reply_text(
f"""
👋 Добро пожаловать, {name}!

✈️ 🚚  AVVALIN CARGO
🇨🇳 Китай → 🇹🇯 Таджикистан

🚀 Быстрое оформление грузов
🔒 Надёжная доставка без рисков
📦 Выгодные тарифы и прозрачная система
""",
reply_markup=menu()
    )


# ================= TEXT =================
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message.text.strip()
    uid = str(update.effective_user.id)

    if uid not in users:
        return

    data = users[uid]

    if "step" not in context.user_data:
        context.user_data["step"] = None

    step = context.user_data.get("step")

    # =================================================
    # FIX: если нажата кнопка меню во время любого шага —
    # сбрасываем сценарий, чтобы бот не путался
    # =================================================
    if msg in MAIN_BUTTONS and step not in ("name", "phone"):
        context.user_data["step"] = None
        step = None

    # ================= REGISTRATION =================
    if step == "name":
        data["name"] = msg
        save_users(users)

        context.user_data["step"] = "phone"

        await update.message.reply_text(
            "📞 Введите ваш телефон:",
            reply_markup=menu()
        )
        return

    if step == "phone":
        data["phone"] = msg
        save_users(users)

        context.user_data["step"] = None

        await update.message.reply_text(
            "✅ Регистрация завершена!",
            reply_markup=menu()
        )
        return


    # ================= PROFILE =================
    if msg == "👤 Профиль":
        await update.message.reply_text(
f"""
👤 {data.get("name","")}
📞 {data.get("phone","")}
🆔 {uid}
📦 Заказов: {len(data.get("orders",[]))}
""",
reply_markup=menu()
        )
        return


    # ================= PRICE =================
    if msg == "💰 Цена":
        context.user_data["step"] = "price"
        await update.message.reply_text(
            "⚖ Введите вес (кг):",
            reply_markup=menu()
        )
        return

    if step == "price":
        try:
            w = float(msg)
            total = w * RATE_PER_KG
            await update.message.reply_text(
f"💰 Стоимость: {total}$",
reply_markup=menu()
            )
        except:
            await update.message.reply_text(
                "❌ Введите число",
                reply_markup=menu()
            )

        context.user_data["step"] = None
        return


    # ================= MY ORDERS (NEW) =================
    if msg == "📋 Мои заказы":

        orders = data.get("orders", [])

        if not orders:
            await update.message.reply_text(
                "📦 У вас пока нет заказов",
                reply_markup=menu()
            )
            return

        text_orders = "📋 Последние заказы:\n\n"

        for o in orders[-5:]:
            text_orders += (
                f"{o['track']} | "
                f"{o['weight']} кг | "
                f"{pretty_status(o['status'])}\n"
            )

        await update.message.reply_text(
            text_orders,
            reply_markup=menu()
        )
        return


    # ================= ORDER =================
    if msg == "📦 Заказ":
        context.user_data["step"] = "from"
        context.user_data["order"] = {}

        await update.message.reply_text(
            "📍 Откуда отправка?",
            reply_markup=menu()
        )
        return

    if step == "from":
        context.user_data["order"]["from"] = msg
        context.user_data["step"] = "to"

        await update.message.reply_text(
            "📍 Куда доставка?",
            reply_markup=menu()
        )
        return

    if step == "to":
        context.user_data["order"]["to"] = msg
        context.user_data["step"] = "weight"

        await update.message.reply_text(
            "⚖ Вес груза?",
            reply_markup=menu()
        )
        return

    if step == "weight":
        try:
            context.user_data["order"]["weight"] = float(msg)
        except:
            await update.message.reply_text(
                "❌ Введите число",
                reply_markup=menu()
            )
            return

        context.user_data["step"] = "desc"

        await update.message.reply_text(
            "📦 Описание груза?",
            reply_markup=menu()
        )
        return

    if step == "desc":

        order = {
            "from": context.user_data["order"]["from"],
            "to": context.user_data["order"]["to"],
            "weight": context.user_data["order"]["weight"],
            "desc": msg,
            "track": make_track(),
            "status": "accepted"
        }

        data["orders"].append(order)
        save_users(users)

        context.user_data.clear()

        await update.message.reply_text(
f"""
✅ Заказ создан

📦 Трек: {order["track"]}
📍 {pretty_status(order["status"])}
""",
reply_markup=menu()
        )
        return


    # ================= STATUS =================
    if msg == "🚚 Статус":

        orders = data.get("orders", [])

        if not orders:
            await update.message.reply_text(
                "❌ Нет заказов",
                reply_markup=menu()
            )
            return

        last = orders[-1]

        await update.message.reply_text(
f"""
🚚 Последний заказ

📦 {last["track"]}
📍 {pretty_status(last["status"])}
""",
reply_markup=menu()
        )
        return


    # ================= TRACK =================
    if msg == "📍 Отследить":
        context.user_data["step"] = "track"

        await update.message.reply_text(
            "🔎 Введите трек номер:",
            reply_markup=menu()
        )
        return

    if step == "track":

        found = None

        for u in users.values():
            for o in u.get("orders", []):
                if o["track"] == msg:
                    found = o
                    break

        if found:
            await update.message.reply_text(
f"""
📦 {found["track"]}
📍 {pretty_status(found["status"])}
""",
reply_markup=menu()
            )
        else:
            await update.message.reply_text(
                "❌ Трек не найден",
                reply_markup=menu()
            )

        context.user_data["step"] = None
        return


    # ================= SUPPORT =================
    if msg == "🆘 Поддержка":
        await update.message.reply_text(
"""📞 Наша поддержка работает 24/7.
💬 Напишите менеджеру — мы ответим быстро.
🚀 Avvalin Cargo всегда рядом с клиентом
""",
reply_markup=menu()
        )
        return


    # ================= CONTACTS NEW =================
    if msg == "📞 Контакты":
        await update.message.reply_text(
"""📞 Контакты

WhatsApp: +992 ...
Telegram: @manager
""",
reply_markup=menu()
        )
        return


    # ================= ABOUT =================
    if msg == "ℹ О компании":
        await update.message.reply_text(
"""✈️ Avvalin Cargo — международная логистическая компания.
🇨🇳 Мы доставляем грузы из Китая в Таджикистан быстро и безопасно.
📦 Наша цель — сделать доставку простой, прозрачной и доступной для каждого клиента.
""",
reply_markup=menu()
        )
        return

    await update.message.reply_text(
        "👇 Используйте меню",
        reply_markup=menu()
    )


# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text
    )
)

print("✈️   AVVALIN CARGO BOT RUNNING...")
app.run_polling()