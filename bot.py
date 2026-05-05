import json
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN as TOKEN

FILE = "data.json"


# ================= DATA =================
def load_users():
    if not os.path.exists(FILE):
        return {}

    if os.path.getsize(FILE) == 0:
        return {}

    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_users(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


users = load_users()


# ================= MENU =================
def menu():
    return ReplyKeyboardMarkup(
        [
            ["📍 Адрес", "📦 VIP"],
            ["🆘 Поддержка"]
        ],
        resize_keyboard=True
    )


def city_menu():
    return ReplyKeyboardMarkup(
        [
            ["Душанбе"],
            ["Панджакент"],
            ["Айни"],
            ["Кумсангир"]
        ],
        resize_keyboard=True
    )


# ================= CITY DATA =================
CITY_DATA = {
    "Душанбе": {
        "code": "01",
        "address": "详细地址：浙江省金华市浦江县河山村A01栋"
    },
    "Панджакент": {
        "code": "02",
        "address": "详细地址：浙江省金华市浦江县河山村A02栋"
    },
    "Айни": {
        "code": "03",
        "address": "详细地址：浙江省金华市浦江县河山村A03栋"
    },
    "Кумсангир": {
        "code": "04",
        "address": "详细地址：浙江省金华市浦江县河山村A04栋"
    }
}


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in users:
        users[uid] = {
            "phone": "",
            "city": "",
            "code": ""
        }
        save_users(users)

        context.user_data["step"] = "phone"

        await update.message.reply_text(
            "📞 Введите ваш номер телефона:"
        )
        return

    await update.message.reply_text(
        "👋 Добро пожаловать!",
        reply_markup=menu()
    )


# ================= TEXT =================
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    uid = str(update.effective_user.id)

    if uid not in users:
        return

    step = context.user_data.get("step")

    # ===== PHONE =====
    if step == "phone":
        users[uid]["phone"] = msg
        save_users(users)

        context.user_data["step"] = "city"

        await update.message.reply_text(
            "🌍 Выберите ваш город:",
            reply_markup=city_menu()
        )
        return

    # ===== CITY =====
    if step == "city":
        if msg not in CITY_DATA:
            return

        city = CITY_DATA[msg]

        users[uid]["city"] = msg
        users[uid]["code"] = city["code"]

        save_users(users)

        context.user_data["step"] = None

        await update.message.reply_text(
            f"""
✅ Сохранено!

📍 Город: {msg}
📦 Код: {city["code"]}

📮 Ваш адрес в Китае:
{city["address"]}
{users[uid]["phone"]} 号
""",
            reply_markup=menu()
        )
        return

    # ===== ADDRESS BUTTON =====
    if msg == "📍 Адрес":
        user = users[uid]

        if not user["city"]:
            await update.message.reply_text("Сначала выберите город")
            return

        city = CITY_DATA[user["city"]]

        await update.message.reply_text(
            f"""
📮 Ваш адрес:

{city["address"]}
{user["phone"]} 号

📍 {user["city"]}
""",
            reply_markup=menu()
        )
        return

    # ===== VIP =====
    if msg == "📦 VIP":
        await update.message.reply_text(
            "💎 VIP клиенты получают лучшие условия и скидки.\nСвяжитесь с менеджером.",
            reply_markup=menu()
        )
        return

    # ===== SUPPORT =====
    if msg == "🆘 Поддержка":
        await update.message.reply_text(
            "📞 Напишите менеджеру: @manager",
            reply_markup=menu()
        )
        return


# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

print("🚀 BOT RUNNING...")
app.run_polling()