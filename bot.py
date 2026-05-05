import json
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
ADMIN_ID = 8373454356  # 👈 твой ID

FILE = "data.json"


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
def get_vip(phone):
    if not phone:
        return "🥉 Bronze"
    if phone.startswith("+992"):
        return "🥈 Silver"
    return "🥇 Gold"


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
            ["📍 Адрес", "👤 Профиль"],
            ["🆘 Поддержка"]
        ],
        resize_keyboard=True
    )


# ================= CITY BUTTONS =================
def city_buttons():
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


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["step"] = "phone"
    await update.message.reply_text("📞 Введите номер телефона:")


# ================= TEXT =================
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    uid = str(update.effective_user.id)

    if uid not in db:
        db[uid] = {}

    step = context.user_data.get("step")

    # ===== PHONE =====
    if step == "phone":
        db[uid]["phone"] = msg
        db[uid]["vip"] = get_vip(msg)
        save_db(db)

        context.user_data["step"] = "city"

        await update.message.reply_text(
            "🏙 Выберите город:",
            reply_markup=city_buttons()
        )
        return

    # ===== SUPPORT =====
    if msg == "🆘 Поддержка":
        await update.message.reply_text(
            "👤 @murtazo7\n📱 +992 90 090 5900"
        )
        return

    # ===== BROADCAST (ADMIN) =====
    if context.user_data.get("step") == "broadcast" and uid == str(ADMIN_ID):
        for u in db.keys():
            try:
                await context.bot.send_message(u, f"📢 {msg}")
            except:
                pass

        context.user_data["step"] = None
        await update.message.reply_text("✅ Отправлено")
        return


# ================= CITY SELECT =================
async def city_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)

    code, addr, city = CITY[query.data]

    db[uid]["city"] = city
    db[uid]["code"] = code
    db[uid]["addr"] = addr

    save_db(db)

    await query.message.reply_text("✅ Город сохранён! Открой 👤 Профиль.")


# ================= PROFILE =================
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    uid = str(update.effective_user.id)

    if msg != "👤 Профиль":
        return

    user = db.get(uid, {})

    phone = user.get("phone", "-")
    city = user.get("city", "")
    vip = user.get("vip", "🥉 Bronze")
    code = user.get("code", "")
    addr = user.get("addr", "")

    if not city:
        await update.message.reply_text("Сначала выберите город")
        return

    text = f"""
✨📦 AVVALIN CARGO

👤 VIP: {vip}

📞 Телефон: {phone}
📍 Город: {city}

收件人：AVALIN
手机号：{phone}
详细地址：浙江省金华市浦江县河山村A{code}栋 ({phone}) 号 {city}
"""

    await update.message.reply_text(text)


# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text("🧑‍💼 ADMIN ACTIVE")


# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
app.add_handler(CallbackQueryHandler(city_select))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, profile))

print("🚀 BOT RUNNING...")
app.run_polling()