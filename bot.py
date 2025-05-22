from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

tables = {}
admin_user_id = 90617694

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == admin_user_id:
        await update.message.reply_text("سلام ادمین! با دستور /newgame یه میز جدید بساز.")
    else:
        if not tables:
            await update.message.reply_text("فعلاً میزی ساخته نشده. منتظر بمون تا ادمین یه میز بسازه.")
            return

        # پیدا کردن آخرین میز
        last_table_id = list(tables.keys())[-1]
        keyboard = [[InlineKeyboardButton("ورود به میز", callback_data=f"join_{last_table_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("برای ورود به بازی روی دکمه زیر بزن:", reply_markup=reply_markup)


async def new_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != admin_user_id:
        await update.message.reply_text("فقط ادمین می‌تونه میز جدید بسازه.")
        return
    table_id = f"table_{len(tables)+1}"
    tables[table_id] = {
        "name": f"میز {len(tables)+1}",
        "players": {},
    }

    keyboard = [[InlineKeyboardButton("ورود به میز", callback_data=f"join_{table_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"{tables[table_id]['name']} ساخته شد!", reply_markup=reply_markup)

async def join_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    table_id = data.split("_", 1)[1]
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.full_name

    tables[table_id]["players"][user_id] = {
        "name": username,
        "charge_count": 0
    }

    keyboard = [[InlineKeyboardButton("💵 منو شارژ کن", callback_data=f"charge_{table_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{username} به {tables[table_id]['name']} اضافه شد.",
        reply_markup=reply_markup
    )

async def charge_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    table_id = query.data.split("_", 1)[1]
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.full_name

    if user_id in tables[table_id]["players"]:
        tables[table_id]["players"][user_id]["charge_count"] += 1
        await context.bot.send_message(
            chat_id=admin_user_id,
            text=f"🧨 {username} درخواست شارژ جدید داد در {tables[table_id]['name']}.\n"
                 f"🔁 تعداد شارژ: {tables[table_id]['players'][user_id]['charge_count']}"
        )
        await query.edit_message_text("✅ درخواست شارژ شما ثبت شد.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != admin_user_id:
        await update.effective_message.reply_text("فقط ادمین به این دسترسی داره.")
        return

    msg = "📊 وضعیت همه میزها:\n\n"
    for table_id, info in tables.items():
        msg += f"🃏 {info['name']}:\n"
        for player in info["players"].values():
            msg += f"  - {player['name']}: {player['charge_count']} شارژ\n"
        msg += "\n"

    await update.effective_message.reply_text(msg)


async def charge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    found_table = None

    # پیدا کردن میزی که این بازیکن توشه
    for table_id, info in tables.items():
        if user_id in info["players"]:
            found_table = (table_id, info)
            break

    if not found_table:
        await update.message.reply_text("شما هنوز عضو هیچ میزی نیستید.")
        return

    table_id, table_info = found_table
    player_info = table_info["players"][user_id]
    charge_count = player_info["charge_count"]

    # ساخت دکمه درخواست شارژ
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 منو شارژ کن", callback_data=f"charge_{table_id}")]
    ])

    await update.message.reply_text(
        f"💰 وضعیت شارژ شما در میز {table_info['name']}:\n"
        f"تعداد شارژ: {charge_count}\n\n"
        f"برای درخواست شارژ جدید دکمه زیر را بزنید 👇",
        reply_markup=keyboard
    )


async def set_bot_commands(application):
    await application.bot.set_my_commands([
        BotCommand("start", "شروع"),
        BotCommand("join", "عضویت در میز"),
        BotCommand("charge", "درخواست شارژ و مشاهده تعداد شارژ"),
        BotCommand("status", "وضعیت همه میزها (فقط ادمین)"),
    ])

app = ApplicationBuilder().token("8073969030:AAGJJiKYpCjTNvpU3aqc6matVvf2s_KNl2w").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("newgame", new_table))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("charge", charge))
app.add_handler(CallbackQueryHandler(join_table, pattern="^join_"))
app.add_handler(CallbackQueryHandler(charge_request, pattern="^charge_"))



# برنامه اصلی
def main():
    app = ApplicationBuilder().token("8073969030:AAGJJiKYpCjTNvpU3aqc6matVvf2s_KNl2w").build()

    # ثبت هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", new_table))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("charge", charge))
    app.add_handler(CallbackQueryHandler(join_table, pattern="^join_"))
    app.add_handler(CallbackQueryHandler(charge_request, pattern="^charge_"))

    # تنظیم کامندها و اجرای بات
    app.post_init = set_bot_commands  # این کلک مهمه! ست کردن async فانکشن بدون اجرای دستی!
    app.run_polling()  # همین کافیه، نیازی به asyncio.run نداری

if __name__ == "__main__":
    main()