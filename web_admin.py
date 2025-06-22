import os
import sqlite3
from flask import Flask, render_template_string, request, redirect
from db import get_top_users, get_latest_draw, get_today_ticket_count
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "lotterysecret")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["logged_in"] = True
            return redirect("/")
        return "❌ Invalid login"
    return '''
    <h2>Admin Login</h2>
    <form method="post">
      <input name="username" placeholder="Username"><br>
      <input name="password" type="password" placeholder="Password"><br>
      <input type="submit" value="Login">
    </form>
    '''

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

def require_login(func):
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route("/")
@require_login
def index():
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("SELECT r.user_id, u.username, r.amount, r.file_id FROM recharges r LEFT JOIN users u ON r.user_id = u.user_id WHERE status='pending'")
    rows = c.fetchall()
    conn.close()
    return render_template_string('''
    <h1>Pending Recharges</h1>
    {% for uid, uname, amt, file in rows %}
    <div style="border:1px solid #ccc; padding:10px; margin:10px;">
      <b>@{{ uname }}</b> (ID: {{ uid }})<br>
      Amount: {{ amt }}<br>
      {% if file %}<img src="https://api.telegram.org/bot{{token}}/getFile?file_id={{ file }}" width="200"><br>{% endif %}
      <a href="/approve/{{ uid }}/{{ amt }}">✅ Approve</a> | <a href="/reject/{{ uid }}">❌ Reject</a>
    </div>
    {% endfor %}
    ''', rows=rows, token=BOT_TOKEN)

@app.route("/approve/<int:user_id>/<int:amount>")
@require_login
def approve(user_id, amount):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    c.execute("UPDATE recharges SET status='approved' WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

    # Notify user
    msg = f"✅ Your recharge of {amount} coins has been approved!"
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", params={
        "chat_id": user_id,
        "text": msg
    })

    return redirect("/")

@app.route("/")
def leaderboard():
    top_users = get_top_users()
    draw = get_latest_draw()
    entries = get_today_ticket_count()
    return render_template("leaderboard.html", users=top_users, draw=draw, entries=entries)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

@app.route("/reject/<int:user_id>")
@require_login
def reject(user_id):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("UPDATE recharges SET status='rejected' WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

    msg = "❌ Your recharge request was rejected by admin."
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", params={
        "chat_id": user_id,
        "text": msg
    })

    return redirect("/")
    
