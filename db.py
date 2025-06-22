import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 100
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
        user_id INTEGER,
        number TEXT,
        draw_date TEXT,
        amount INTEGER,
        UNIQUE(draw_date, number)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS draws (
        draw_date TEXT PRIMARY KEY,
        winning_number TEXT,
        winner_id INTEGER
    )''')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def update_balance(user_id, amount):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def buy_ticket(user_id, number, draw_date, amount):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    try:
        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = c.fetchone()[0]
        if balance < amount:
            return "❌ Insufficient balance."
        c.execute("SELECT 1 FROM tickets WHERE draw_date=? AND number=?", (draw_date, number))
        if c.fetchone():
            return "❌ Number already taken."
        c.execute("INSERT INTO tickets (user_id, number, draw_date, amount) VALUES (?, ?, ?, ?)", (user_id, number, draw_date, amount))
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id))
        conn.commit()
        return "✅ Ticket purchased."
    except:
        return "❌ Error occurred."
    finally:
        conn.close()

def get_users_by_number(draw_date, winning_number):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM tickets WHERE draw_date=? AND number=?", (draw_date, winning_number))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def record_draw(draw_date, winning_number, winner_id):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("INSERT INTO draws VALUES (?, ?, ?)", (draw_date, winning_number, winner_id))
    conn.commit()
    conn.close()

def transfer_balance(sender_id, receiver_username, amount):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE username=?", (receiver_username,))
    receiver = c.fetchone()
    if not receiver:
        return "❌ Receiver not found."
    receiver_id = receiver[0]
    c.execute("SELECT balance FROM users WHERE user_id=?", (sender_id,))
    sender_balance = c.fetchone()[0]
    if sender_balance < amount:
        return "❌ Insufficient balance."
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, sender_id))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, receiver_id))
    conn.commit()
    conn.close()
    return f"✅ Sent {amount} coins to @{receiver_username}"

def get_top_users(limit=10):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
    result = c.fetchall()
    conn.close()
    return result

def get_latest_draw():
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("SELECT draw_date, winning_number, winner_id FROM draws ORDER BY draw_date DESC LIMIT 1")
    draw = c.fetchone()
    if not draw:
        return None
    date, number, winner_id = draw
    c.execute("SELECT username FROM users WHERE user_id=?", (winner_id,))
    winner = c.fetchone()
    conn.close()
    return {
        "date": date,
        "number": number,
        "winner": winner[0] if winner else "No Winner"
    }

def get_today_ticket_count():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tickets WHERE draw_date=?", (today,))
    count = c.fetchone()[0]
    conn.close()
    return count