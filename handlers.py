import random
from telegram import *
from telegram.ext import *
from db import cur, conn
from config import ADMIN_ID, RATE_PER_KG


STATUSES = {
"accepted":"📦 Принят на складе",
"transit":"✈️ В пути",
"customs":"🛃 На таможне",
"tj":"🇹🇯 Прибыл в Таджикистан",
"ready":"✅ Готов к выдаче"
}


def menu():
    return ReplyKeyboardMarkup(
        [
         ["📦 Заказ","👤 Профиль"],
         ["💰 Цена","🆔 Мой ID"],
         ["🚚 Статус","📍 Отследить"],
         ["🆘 Поддержка","ℹ О компании"]
        ],
        resize_keyboard=True
    )


def make_track():
    return f"AV{random.randint(100000,999999)}"


async def start(update:Update,context):
    user=update.effective_user

    cur.execute(
      "SELECT * FROM users WHERE id=?",
      (user.id,)
    )

    if not cur.fetchone():
        cur.execute(
        "INSERT INTO users VALUES(?,?,?)",
        (
         user.id,
         user.full_name,
         None
        ))
        conn.commit()

    await update.message.reply_text(
        "✈️ AVVALIN CARGO\n"
        "🇨🇳 Китай → 🇹🇯 Таджикистан\n\n"
        "🚀 Быстро | 🔒 Надежно | 📦 Выгодно",
        reply_markup=menu()
    )


async def admin(update,context):

    if update.effective_user.id!=ADMIN_ID:
        return

    await update.message.reply_text(
"""
🧑‍💼 ADMIN PANEL

/orders
/users
/setrate 6
/broadcast text
"""
)


async def users(update,context):

    if update.effective_user.id!=ADMIN_ID:
        return

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    txt="👤 USERS\n\n"

    for r in rows:
        txt+=f"{r[1]} | {r[0]}\n"

    await update.message.reply_text(txt)



async def orders(update,context):

    if update.effective_user.id!=ADMIN_ID:
        return

    cur.execute("""
    SELECT track,status
    FROM orders
    """)

    rows=cur.fetchall()

    if not rows:
        await update.message.reply_text(
        "Нет заказов"
        )
        return

    txt="📦 ORDERS\n\n"

    for r in rows:
        txt+=f"{r[0]} {r[1]}\n"

    await update.message.reply_text(txt)



async def broadcast(update,context):

    if update.effective_user.id!=ADMIN_ID:
        return

    msg=" ".join(context.args)

    cur.execute("SELECT id FROM users")
    rows=cur.fetchall()

    for u in rows:
        try:
            await context.bot.send_message(
                u[0],
                f"📢 {msg}"
            )
        except:
            pass

    await update.message.reply_text(
        "Рассылка отправлена"
    )


async def text(update,context):

    msg=update.message.text
    user=update.effective_user


    if context.user_data.get("step")=="price":

        try:
            w=float(msg)

            await update.message.reply_text(
            f"{w} кг = {w*RATE_PER_KG}$"
            )

        except:
            await update.message.reply_text(
            "Введите число"
            )

        context.user_data["step"]=None
        return


    if msg=="💰 Цена":
        context.user_data["step"]="price"
        await update.message.reply_text(
            "Введите вес:"
        )
        return


    if msg=="🆔 Мой ID":
        await update.message.reply_text(
            str(user.id)
        )
        return


    if msg=="👤 Профиль":

        cur.execute(
        "SELECT * FROM users WHERE id=?",
        (user.id,)
        )

        u=cur.fetchone()

        await update.message.reply_text(
f"""
Имя: {u[1]}
Телефон: {u[2] or '-'}
ID: {u[0]}
"""
)
        return


    if msg=="📦 Заказ":
        context.user_data["step"]="from"
        context.user_data["order"]={}
        await update.message.reply_text(
        "Откуда?"
        )
        return


    if context.user_data.get("step")=="from":
        context.user_data["order"]["from"]=msg
        context.user_data["step"]="to"
        await update.message.reply_text(
        "Куда?"
        )
        return


    if context.user_data.get("step")=="to":
        context.user_data["order"]["to"]=msg
        context.user_data["step"]="weight"

        await update.message.reply_text(
        "Вес?"
        )
        return


    if context.user_data.get("step")=="weight":
        context.user_data["order"]["weight"]=msg
        context.user_data["step"]="desc"

        await update.message.reply_text(
        "Описание?"
        )
        return


    if context.user_data.get("step")=="desc":

        o=context.user_data["order"]

        track=make_track()

        cur.execute("""
        INSERT INTO orders(
        track,
        user_id,
        from_city,
        to_city,
        weight,
        description,
        status
        )
        VALUES(?,?,?,?,?,?,?)
        """,
        (
        track,
        user.id,
        o["from"],
        o["to"],
        o["weight"],
        msg,
        "accepted"
        ))

        conn.commit()

        context.user_data["step"]=None

        await update.message.reply_text(
f"""
✅ Заказ создан

Трек:
{track}

Статус:
{STATUSES["accepted"]}
""",
reply_markup=menu()
)
        return



    if msg=="🚚 Статус":

        cur.execute("""
        SELECT track,status
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC LIMIT 1
        """,(user.id,))

        row=cur.fetchone()

        if not row:
            await update.message.reply_text(
            "Нет заказов"
            )
            return

        await update.message.reply_text(
f"""
📦 {row[0]}
{STATUSES[row[1]]}
"""
)
        return


    if msg=="📍 Отследить":
        context.user_data["step"]="track"
        await update.message.reply_text(
        "Введите трек:"
        )
        return


    if context.user_data.get("step")=="track":

        tr=msg

        cur.execute("""
        SELECT status
        FROM orders
        WHERE track=?
        """,(tr,))

        row=cur.fetchone()

        if row:
            await update.message.reply_text(
            STATUSES[row[0]]
            )
        else:
            await update.message.reply_text(
            "Трек не найден"
            )

        context.user_data["step"]=None
        return


    if msg=="🆘 Поддержка":
        await update.message.reply_text(
        "Свяжитесь с менеджером"
        )
        return


    if msg=="ℹ О компании":
        await update.message.reply_text(
        "Avvalin Cargo логистика Китай→Таджикистан"
        )
        return