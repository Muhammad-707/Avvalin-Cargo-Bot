import json
import os
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
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


# ================= GOOGLE SHEETS (OPTIONAL) =================
# pip install gspread oauth2client
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    CREDS = ServiceAccountCredentials.from_json_keyfile_name("google.json", SCOPE)
    GSHEET = gspread.authorize(CREDS)
    SHEET = GSHEET.open("AvvalinCargo").sheet1
except:
    SHEET = None


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


# ================= VIP =================
def vip(phone):
    if not phone:
        return "🥉 Bronze"
    if phone.startswith("+992"):
        return "🥈 Silver"
    return "🥇 Gold"


# ================= TRACK =================
def make_track():
    return f"AV{datetime.now().strftime('%H%M%S')}"


# ================= CITY =================
CITY = {
    "dushanbe": ("01", "A01", "Душанбе"),
    "paj": ("02", "A02", "Панджакент"),
    "aini": ("03", "A03", "Айни"),
    "kums": ("04", "A04", "Кумсангир")
}


# ================= UI (TEMU STYLE) =================
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
            InlineKeyboardButton("✨ Душанбе", callback_data="dushanbe"),
            InlineKeyboardButton("✨ Панджакент", callback_data="paj")
        ],
        [
            InlineKeyboardButton("✨ Айни", callback_data="aini"),
            InlineKeyboardButton("✨ Кумсангир", callback_data="kums")
        ]
    ])


# ================= SAVE ORDER =================
def save_to_sheets(row):
    if SHEET:
        SHEET.append_row(row)


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["step"] = "phone"
    await update.message.reply_text("📞 Введите номер телефона:", reply_markup=menu())


# ================= AUTO NOTIFY =================
async def notify_user(context, uid, text):
    try:
        await context.bot.send_message(uid, text)
    except:
        pass


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

        context.user_data["step"] = "city"

        await update.message.reply_text("🏙 Выберите город:", reply_markup=city_ui())
        return

    # ===== NEW ORDER =====
    if msg == "🛒 Новый заказ":
        context.user_data["step"] = "city"
        await update.message.reply_text("🏙 Выберите город:", reply_markup=city_ui())
        return

    # ===== PROFILE =====
    if msg == "👤 Профиль":
        u = db.get(uid, {})
        await update.message.reply_text(f"""
👤 PROFILE

📞 {u.get('phone','-')}
💎 {u.get('vip','Bronze')}
📦 Orders: {len(u.get('orders',[]))}
""")
        return

    # ===== ORDERS =====
    if msg == "📦 Мои заказы":
        orders = db.get(uid, {}).get("orders", [])
        if not orders:
            await update.message.reply_text("Нет заказов")
            return

        text = "📦 ORDERS:\n\n"
        for o in orders[-5:]:
            text += o["track"] + " | " + o["status"] + "\n"

        await update.message.reply_text(text)
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
            f"📦 {found['track']} - {found['status']}" if found else "Не найден"
        )
        context.user_data["step"] = None
        return


# ================= CITY SELECT =================
async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = str(q.from_user.id)

    code, addr, city = CITY[q.data]
    phone = db.get(uid, {}).get("phone", "-")

    track = make_track()

    order_text = f"""
收件人：AVALIN
手机号：{phone}
详细地址：浙江省金华市浦江县河山村{addr}栋 ({phone}) 号 {city}
"""

    order = {
        "track": track,
        "status": "accepted",
        "text": order_text
    }

    db[uid]["orders"].append(order)
    save_db(db)

    # GOOGLE SHEETS
    save_to_sheets([uid, track, phone, city, order_text, str(datetime.now())])

    # AUTO NOTIFY
    await notify_user(context, uid, f"✅ Заказ создан: {track}")

    await q.message.reply_text(order_text)


# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    total = len(db)

    await update.message.reply_text(f"""
🧑‍💼 ADMIN PANEL

👤 Users: {total}
📦 Orders: {sum(len(u.get('orders',[])) for u in db.values())}
""")


# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
app.add_handler(CallbackQueryHandler(city))

print("🚀 NEXT LEVEL BOT RUNNING...")
app.run_polling()