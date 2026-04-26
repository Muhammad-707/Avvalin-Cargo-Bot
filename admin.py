from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from users import users

# ===== ADMIN PANEL =====
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Нет доступа")
        return

    total_users = len(users)

    await update.message.reply_text(
        "🧑‍💼 ADMIN PANEL\n\n"
        f"👤 Users: {total_users}\n"
        "📦 Orders: stored in system\n\n"
        "Commands:\n"
        "/users - список пользователей"
    )


# ===== LIST USERS =====
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        return

    if not users:
        await update.message.reply_text("Нет пользователей")
        return

    text = "👤 USERS LIST:\n\n"

    for uid, data in users.items():
        text += (
            f"ID: {uid}\n"
            f"Name: {data.get('name','-')}\n"
            f"Phone: {data.get('phone','-')}\n"
            "-----------------\n"
        )

    await update.message.reply_text(text)