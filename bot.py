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
ADMIN_ID = 8373458315  # 👈 ОДИН АДМИН

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


# ================= VIP SYSTEM =================
def get_vip(phone):
    if not phone:
        return "🥉 Bronze"
    if phone.startswith("+992"):
        return "🥈 Silver"
    return "🥇 Gold"


# ================= CITY DATA =================
CITY = {
    "dushanbe": ("01", "A01", "Душанбе"),
    "paj": ("02", "A02", "Панджакент"),
    "aini": ("03", "A03", "Айни"),
    "kums": ("04", "A04", "Кумсангир")
}


# ================= GLASS UI BUTTONS =================
def city_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✨🫧 Душанбе", callback_data="dushanbe"),
            InlineKeyboardButton("✨🫧 Панджакент", callback_data="paj")
        ],
        [
            InlineKeyboardButton("✨🫧 Айни", callback_data="aini"),
            InlineKeyboardButton("✨🫧 Кумсангир", callback_data="kums")
        ]
    ])


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Users", callback_data="users")],
        [InlineKeyboardButton("📦 Orders", callback_data="orders")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")]
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
        db[uid] = {"orders": []}

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

    # ===== BROADCAST =====
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
    phone = db.get(uid, {}).get("phone", "")
    vip = db.get(uid, {}).get("vip", "🥉 Bronze")

    text_result = f"""
✨📦 AVVALIN CARGO

👤 VIP: {vip}

收件人：AVALIN
手机号：{phone}
详细地址：浙江省金华市浦江县河山村{addr}栋 ({phone}) 号 {city}
"""

    if "orders" not in db[uid]:
        db[uid]["orders"] = []

    db[uid]["orders"].append(text_result)
    db[uid]["last_order"] = text_result

    save_db(db)

    await query.message.reply_text(text_result)


# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text("🧑‍💼 ADMIN PANEL", reply_markup=admin_menu())


# ================= CALLBACK =================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)

    # ===== USERS =====
    if query.data == "users" and uid == str(ADMIN_ID):
        text = "👤 USERS:\n\n"
        for u, d in db.items():
            text += f"{u} | {d.get('phone','-')} | {d.get('vip','-')}\n"
        await query.message.reply_text(text)

    # ===== ORDERS =====
    elif query.data == "orders" and uid == str(ADMIN_ID):
        text = "📦 ORDERS:\n\n"
        for u, d in db.items():
            for o in d.get("orders", []):
                text += o + "\n-----------------\n"
        await query.message.reply_text(text)

    # ===== BROADCAST =====
    elif query.data == "broadcast" and uid == str(ADMIN_ID):
        context.user_data["step"] = "broadcast"
        await query.message.reply_text("📢 Введите сообщение")


# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
app.add_handler(CallbackQueryHandler(city_select))
app.add_handler(CallbackQueryHandler(callback))

print("🚀 PRO BOT RUNNING...")
app.run_polling()