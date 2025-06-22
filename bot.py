from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from db import init_db, add_user, get_balance, buy_ticket, transfer_balance
from draw import perform_draw
from config import BOT_TOKEN, ADMINS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import sqlite3
import os

init_db()
app = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)
    await update.message.reply_text("🎉 Welcome to the Lottery Bot! Use /buy 4digit_number amount to participate.")

async def recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        return await update.message.reply_text("Usage: /recharge 100")
    amount = int(context.args[0])
    user_id = update.effective_user.id
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO recharges (user_id, amount, status, timestamp) VALUES (?, ?, ?, ?)",
              (user_id, amount, 'pending', datetime.now().isoformat()))
    conn.commit()
    conn.close()
    await update.message.reply_text("📨 Recharge request submitted. Send proof with /deposit_proof.")

async def deposit_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        user_id = update.effective_user.id
        conn = sqlite3.connect("lottery.db")
        c = conn.cursor()
        c.execute("UPDATE recharges SET file_id=? WHERE user_id=? AND status='pending'", (file_id, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text("✅ Proof received. Awaiting admin approval.")
        for admin in ADMINS:
            await context.bot.send_photo(chat_id=admin, photo=file_id, caption=f"📥 Recharge proof from @{update.effective_user.username}")
    else:
        await update.message.reply_text("❌ Please send an image after /deposit_proof.")

async def cancel_recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("DELETE FROM recharges WHERE user_id=? AND status='pending'", (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("❌ Recharge request cancelled.")
    
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
    msg = (
        f"🎯 Draw Completed!
"
        f"Winning Number: {result['number']}
"
        f"Winner: {result['winner'] or 'No winner'}"
    )
    await update.message.reply_text(msg)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from db import get_top_users
    top = get_top_users()
    msg = "🏆 Top Users:

"
    for i, (username, balance) in enumerate(top, 1):
        msg += f"{i}. @{username or 'Unknown'} — {balance} coins
"
    await update.message.reply_text(msg)

async def recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        return await update.message.reply_text("🪙 Usage: /recharge 100")
    amount = int(context.args[0])
    await update.message.reply_text(f"📨 Recharge request of {amount} coins sent to admin.")
    for admin_id in ADMINS:
        await context.bot.send_message(
            admin_id,
            f"💳 Recharge Request
User: @{update.effective_user.username}
ID: {update.effective_user.id}
Amount: {amount}"
        )

async def recharge_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("❌ You are not authorized.")
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /recharge_user @username amount")
    username = context.args[0].replace("@", "")
    amount = int(context.args[1])
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if not user:
        return await update.message.reply_text("❌ User not found.")
    user_id = user[0]
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Recharged {amount} coins to @{username}")

async def mytickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("SELECT draw_date, number, amount FROM tickets WHERE user_id=? ORDER BY draw_date DESC", (user_id,))
    tickets = c.fetchall()
    conn.close()
    if not tickets:
        return await update.message.reply_text("🎟 You haven't bought any tickets yet.")
    msg = "🎟 Your Tickets:

"
    for date, number, amt in tickets:
        msg += f"📅 {date} — #{number} ({amt} coins)
"
    await update.message.reply_text(msg)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("send", send_coins))
app.add_handler(CommandHandler("draw", draw_now))
app.add_handler(CommandHandler("leaderboard", leaderboard))
app.add_handler(CommandHandler("recharge", recharge))
app.add_handler(CommandHandler("recharge_user", recharge_user))
app.add_handler(CommandHandler("mytickets", mytickets))
app.add_handler(CommandHandler("deposit_proof", deposit_proof))
app.add_handler(CommandHandler("cancel_recharge", cancel_recharge))
app.add_handler(MessageHandler(filters.PHOTO, deposit_proof))

scheduler = BackgroundScheduler()
scheduler.add_job(perform_draw, 'cron', hour=21, minute=0)
scheduler.start()

app.run_polling()
