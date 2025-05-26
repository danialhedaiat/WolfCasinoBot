import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

from admin import Admin
from member import Member
from table import Table

tables: list[Table] = []

super_user = os.getenv("SUPER_USER")
super_id = os.getenv("SUPER_ID")
super_admin = Admin(telegram_username=super_user, telegram_id=super_id)

admins: list[Admin] = []

members: list[Member] = []


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.username

    if user_id == super_admin.telegram_username:
        await update.message.reply_text("سلام ادمین! با دستور /newgame یه میز جدید بساز.")
    else:
        if not tables:
            await update.message.reply_text("فعلاً میزی ساخته نشده. منتظر بمون تا ادمین یه میز بسازه.")
            return


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.username
    if user_id != super_admin.telegram_username and user_id not in [admin.telegram_username for admin in admins]:
        await update.message.reply_text("فقط ادمین می‌تونه همه چیز رو ریست کنه.")
        return


    tables.clear()
    members.clear()

    await context.bot.send_message(chat_id=super_admin.telegram_id, text="همه چیز ریست شد!")

async def new_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.username
    if user_id != super_admin.telegram_username:
        await update.message.reply_text("فقط ادمین می‌تونه ادمین جدید اضافه کنه.")
        return

    new_admin_username = context.args[0] if context.args else None
    if not new_admin_username:
        await update.message.reply_text("لطفاً نام کاربری ادمین جدید را وارد کنید.")
        return

    member = next((member for member in members if member.telegram_username == new_admin_username), None)
    if not member:
        await update.message.reply_text(f"کاربری با نام {new_admin_username} پیدا نشد. لطفاً ابتدا کاربر را به یک میز اضافه کنید.")
        return

    new_admin = Admin(telegram_username=new_admin_username, telegram_id=member.telegram_id)
    admins.append(new_admin)

    await update.message.reply_text(f"ادمین جدید {new_admin_username} اضافه شد!")


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.username
    keyboard = [
        [InlineKeyboardButton(f"ورود به میز {table.table_id}", callback_data=f"join_{table.table_id}") for table in
         tables]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("لطفاً یکی از میزها را انتخاب کنید:", reply_markup=reply_markup)


async def new_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.username
    if user_id != super_admin.telegram_username and user_id not in [admin.telegram_username for admin in admins]:
        await update.message.reply_text("فقط ادمین می‌تونه میز جدید بسازه.")
        return

    table = Table()
    tables.append(table)

    keyboard = [[InlineKeyboardButton(f"ورود به میز {table.table_id}", callback_data=f"join_{table.table_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"{table.table_id} ساخته شد!", reply_markup=reply_markup)


async def join_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    table_id = data.split("_", 1)[1]
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.full_name

    member = Member(telegram_username=username, telegram_id=user_id)
    if member.telegram_username in tuple(member.telegram_username for member in members):
        await query.edit_message_text("شما در این میز حضور دارید.")
        return
    members.append(member)

    table = next((table for table in tables if str(table.table_id) == table_id), None)
    if not table:
        await query.edit_message_text("میز مورد نظر پیدا نشد.")
        return
    table.add_member(member.telegram_username)

    keyboard = [[InlineKeyboardButton("💵 منو شارژ کن", callback_data=f"charge_{member.telegram_username}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{username} به میز {table_id} اضافه شد.",
        reply_markup=reply_markup
    )


async def charge_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.full_name

    member = next((member for member in members if member.telegram_username == username), None)
    if not member:
        await query.edit_message_text("شما هنوز به هیچ میزی نپیوسته‌اید. لطفاً ابتدا به یک میز بپیوندید.")
        return
    member.increace_charge()

    await update.effective_message.reply_text("شارژ شما با موفقیت ثبت شد! 💰\n")

    notify_text = f"درخواست شارژ جدید توسط {username} ثبت شد."
    await context.bot.send_message(chat_id=super_admin.telegram_id, text=notify_text)
    for admin in admins:
        await context.bot.send_message(chat_id=admin.telegram_id, text=notify_text)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.username
    if user_id != super_admin.telegram_username and user_id not in [
        admin.telegram_username for
        admin in admins]:
        await update.effective_message.reply_text("فقط ادمین به این دسترسی داره.")
        return

    msg = "📊 وضعیت همه میزها:\n\n"
    for member in members:
        msg += f"🃏 {member.telegram_username}:\n"
        msg += f"  - {member.charge_count} شارژ\n"
        msg += "\n"

    await update.effective_message.reply_text(msg)


async def charge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.username

    if user_id not in [member.telegram_username for member in members]:
        await update.message.reply_text("شما هنوز به هیچ میزی نپیوسته‌اید. لطفاً ابتدا به یک میز بپیوندید.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 منو شارژ کن", callback_data=f"charge_")]
    ])
    member = next((member for member in members if member.telegram_username == user_id), None)

    await update.message.reply_text(
        f"💰 وضعیت شارژ شما :\n"
        f"تعداد شارژ: {member.charge_count}\n\n"
        f"برای درخواست شارژ جدید دکمه زیر را بزنید 👇",
        reply_markup=keyboard
    )


async def set_bot_commands(application):
    await application.bot.set_my_commands([
        BotCommand("start", "شروع"),
        BotCommand("join", "عضویت در میز"),
        BotCommand("charge", "درخواست شارژ و مشاهده تعداد شارژ"),
        BotCommand("admin", "اضافه کردن ادمین جدید (فقط ادمین)"),
        BotCommand("restart", "ری استارت (فقط ادمین)"),
        BotCommand("newgame", "ساخت میز جدید (فقط ادمین)"),
        BotCommand("status", "وضعیت همه میزها (فقط ادمین)"),
    ])


def main():
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # ثبت هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", new_admin))
    app.add_handler(CommandHandler("newgame", new_table))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("charge", charge))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CallbackQueryHandler(join_table, pattern="^join_"))
    app.add_handler(CallbackQueryHandler(charge_request, pattern="^charge_"))

    app.post_init = set_bot_commands
    app.run_polling()


if __name__ == "__main__":
    main()
