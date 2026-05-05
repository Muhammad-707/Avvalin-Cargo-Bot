import json
import os
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN

# ================= ADMIN =================
ADMIN_ID = 8373454356

FILE = "data.json"


# ================= GOOGLE SHEETS (optional) =================
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "google.json",
        scope
    )

    client = gspread.authorize(creds)
    sheet = client.open("AvvalinCargo").sheet1

except:
    sheet = None


# ================= DB =================
def load_db():
    if os.path.exists(FILE):
        try:
            with open(FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_db(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


db = load_db()


# ================= CITY =================
CITY = {
    "dushanbe": ("01", "A01", "Душанбе"),
    "paj": ("02", "A02", "Панджакент"),
    "aini": ("03", "A03", "Айни"),
    "kums": ("04", "A04", "Кумсангир")
}


# ================= MENU =================
def menu():
    return ReplyKeyboardMarkup(
        [
            ["🛒 Новый заказ", "👤 Профиль"],
            ["📦 Мои заказы", "📍 Отследить"],
            ["🆘 Поддержка"]
        ],
        resize_keyboard=True
    )


def city_ui():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Душанбе", callback_data="dushanbe"),
            InlineKeyboardButton("Панджакент", callback_data="paj")
        ],
        [
            InlineKeyboardButton("Айни", callback_data="aini"),
            InlineKeyboardButton("Кумсангир", callback_data="kums")
        ]
    ])


# ================= HELPERS =================
def make_track():
    return f"AV{datetime.now().strftime('%H%M%S')}"


def vip(phone):
    if not phone:
        return "🥉 Bronze"
    if phone.startswith("+992"):
        return "🥈 Silver"
    return "🥇 Gold"


def notify(context, uid, text):
    try:
        return context.bot.send_message(uid, text)
    except:
        pass


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in db:
        db[uid] = {"orders": []}
        save_db(db)

    context.user_data["step"] = "phone"

    await update.message.reply_text("📞 Введите номер телефона:")


# ================= TEXT =================
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    uid = str(update.effective_user.id)

    if uid not in db:
        db[uid] = {"orders": []}

    step = context.user_data.get("step")

    # ===== PHONE =====
    if step == "phone":
        db[uid]["phone"] = msg
        db[uid]["vip"] = vip(msg)
        save_db(db)

        context.user_data["step"] = None

        await update.message.reply_text(
            "🏙 Выберите город:",
            reply_markup=city_ui()
        )
        return

    # ===== NEW ORDER =====
    if msg == "🛒 Новый заказ":
        context.user_data["step"] = "phone"
        await update.message.reply_text("📞 Введите номер телефона:")
        return

    # ===== PROFILE =====
    if msg == "👤 Профиль":
        u = db.get(uid, {})
        await update.message.reply_text(f"""
👤 Профиль

📞 {u.get('phone','-')}
💎 {u.get('vip','Bronze')}
📦 Заказов: {len(u.get('orders',[]))}
""")
        return

    # ===== ORDERS =====
    if msg == "📦 Мои заказы":
        orders = db.get(uid, {}).get("orders", [])

        if not orders:
            await update.message.reply_text("Нет заказов")
            return

        text = "📦 Заказы:\n\n"
        for o in orders[-5:]:
            text += f"{o['track']} | {o['status']}\n"

        await update.message.reply_text(text)
        return

    # ===== SUPPORT =====
    if msg == "🆘 Поддержка":
        await update.message.reply_text(
            "👤 @murtazo7\n📱 +992 90 090 5900"
        )
        return

    # ===== TRACK =====
    if msg == "📍 Отследить":
        context.user_data["step"] = "track"
        await update.message.reply_text("Введите трек:")
        return

    if step == "track":
        found = None

        for u in db.values():
            for o in u.get("orders", []):
                if o["track"] == msg:
                    found = o

        await update.message.reply_text(
            f"📦 {found['track']} | {found['status']}" if found else "Не найден"
        )

        context.user_data["step"] = None
        return


# ================= CITY CALLBACK =================
async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = str(q.from_user.id)

    code, addr, city_name = CITY[q.data]
    phone = db.get(uid, {}).get("phone", "-")

    if "orders" not in db[uid]:
        db[uid]["orders"] = []

    track = make_track()

    order_text = f"""
收件人：AVALIN
手机号：{phone}
详细地址：浙江省金华市浦江县河山村{addr}栋 ({phone}) 号 {city_name}
"""

    order = {
        "track": track,
        "status": "accepted",
        "text": order_text
    }

    db[uid]["orders"].append(order)
    save_db(db)

    # Google Sheets
    if sheet:
        sheet.append_row([
            uid,
            track,
            phone,
            city_name,
            order_text,
            str(datetime.now())
        ])

    await notify(context, uid, f"✅ Заказ создан: {track}")

    await q.message.reply_text(order_text)


# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    total_users = len(db)
    total_orders = sum(len(u.get("orders", [])) for u in db.values())

    await update.message.reply_text(f"""
🧑‍💼 ADMIN

👤 Users: {total_users}
📦 Orders: {total_orders}
""")


# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
app.add_handler(CallbackQueryHandler(city, pattern="^(dushanbe|paj|aini|kums)$"))

print("🚀 BOT RUNNING...")
app.run_polling()