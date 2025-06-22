import random
import sqlite3
from datetime import datetime
from db import update_balance, record_draw

def perform_draw():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()

    c.execute("SELECT number FROM tickets WHERE draw_date=?", (today,))
    numbers = [row[0] for row in c.fetchall()]
    if not numbers:
        return {"number": "----", "winner": None}

    winning_number = random.choice(numbers)
    c.execute("SELECT user_id, amount, number FROM tickets WHERE draw_date=?", (today,))
    tickets = c.fetchall()

    total_pool = sum(row[1] for row in tickets)
    prize_pool = int(total_pool * 0.9)
    first_prize = int(prize_pool * 0.5)
    remaining_prize = prize_pool - first_prize

    winner_id = None
    for uid, amt, num in tickets:
        if num == winning_number:
            winner_id = uid
            update_balance(uid, first_prize)
            break

    for uid, amt, num in tickets:
        if uid != winner_id:
            share = int((amt / total_pool) * remaining_prize)
            update_balance(uid, share)

    record_draw(today, winning_number, winner_id)
    conn.close()
    return {"number": winning_number, "winner": winner_id}