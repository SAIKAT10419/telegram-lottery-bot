from flask import Flask, render_template
from db import get_top_users, get_latest_draw, get_today_ticket_count

app = Flask(__name__)

@app.route("/")
def leaderboard():
    top_users = get_top_users()
    draw = get_latest_draw()
    entries = get_today_ticket_count()
    return render_template("leaderboard.html", users=top_users, draw=draw, entries=entries)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)