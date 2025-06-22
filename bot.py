from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from db import init_db, add_user, get_balance, buy_ticket, transfer_balance
from draw import perform_draw
from config import BOT_TOKEN, ADMINS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

init_db()
app = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)
    await update.message.reply_text("🎉 Welcome to the Lottery Bot!
Use /buy 4digit_number amount to participate.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = get_balance(update.effective_user.id)
    await update.message.reply_text(f"💰 Your Balance: {bal} coins")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1 or not context.args[0].isdigit() or len(context.args[0]) != 4:
        await update.message.reply_text("❌ Usage: /buy 1234 [amount]")
        return

    number = context.args[0]
    amount = int(context.args[1]) if len(context.args) > 1 else 10
    today = datetime.now().strftime("%Y-%m-%d")
    result = buy_ticket(update.effective_user.id, number, today, amount)
    await update.message.reply_text(result)

async def send_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        username = context.args[0].replace("@", "")
        amount = int(context.args[1])
    except:
        await update.message.reply_text("❌ Usage: /send @username 10")
        return

    response = transfer_balance(update.effective_user.id, username, amount)
    await update.message.reply_text(response)

async def draw_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    result = perform_draw()
    await update.message.reply_text(f"🎯 Draw Completed!
Winning Number: {result['number']}
Winner: {result['winner'] or 'No winner'}")

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("send", send_coins))
app.add_handler(CommandHandler("draw", draw_now))

scheduler = BackgroundScheduler()
scheduler.add_job(perform_draw, 'cron', hour=21, minute=0)
scheduler.start()

app.run_polling()