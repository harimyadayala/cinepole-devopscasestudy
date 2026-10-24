"""CineBook - Movie Ticket Booking System (Flask)."""
import os
import threading
import uuid
from datetime import datetime

from flask import Flask, abort, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

_lock = threading.Lock()

ROWS = "ABCDEF"
SEATS_PER_ROW = 8
PRICE_PER_SEAT = 250  # INR

MOVIES = {
    1: {"title": "Galaxy Runners", "genre": "Sci-Fi", "duration": "2h 15m", "rating": "8.1",
        "language": "English", "shows": ["10:00 AM", "02:00 PM", "07:30 PM"],
        "desc": "A crew of smugglers races across star systems to deliver a cargo that could end a war."},
    2: {"title": "Monsoon Melody", "genre": "Romance", "duration": "2h 05m", "rating": "7.6",
        "language": "Telugu", "shows": ["11:00 AM", "03:30 PM", "08:00 PM"],
        "desc": "Two musicians from rival towns discover love during one rain-soaked festival season."},
    3: {"title": "The Last Heist", "genre": "Thriller", "duration": "2h 30m", "rating": "8.4",
        "language": "Hindi", "shows": ["12:00 PM", "04:00 PM", "09:00 PM"],
        "desc": "A retired thief is pulled back for one final job that is not what it seems."},
    4: {"title": "Funny Bones", "genre": "Comedy", "duration": "1h 55m", "rating": "7.2",
        "language": "English", "shows": ["10:30 AM", "01:30 PM", "06:00 PM"],
        "desc": "A clumsy museum guard accidentally becomes the hero of a dinosaur-sized mix-up."},
}

# (movie_id, show) -> set of booked seat labels
BOOKED = {}
# booking_id -> booking dict
BOOKINGS = {}


def all_seats():
    return [f"{r}{n}" for r in ROWS for n in range(1, SEATS_PER_ROW + 1)]


def get_movie_or_404(movie_id):
    movie = MOVIES.get(movie_id)
    if not movie:
        abort(404)
    return movie


@app.route("/")
def index():
    return render_template("index.html", movies=MOVIES)


@app.route("/movie/<int:movie_id>", methods=["GET", "POST"])
def movie(movie_id):
    m = get_movie_or_404(movie_id)
    show = request.values.get("show", m["shows"][0])
    if show not in m["shows"]:
        show = m["shows"][0]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        seats = request.form.getlist("seats")
        valid = set(all_seats())

        if not name or "@" not in email:
            flash("Please enter a valid name and email.", "error")
        elif not seats or not set(seats) <= valid:
            flash("Please select at least one valid seat.", "error")
        else:
            with _lock:
                taken = BOOKED.setdefault((movie_id, show), set())
                clash = taken & set(seats)
                if clash:
                    flash(f"Seat(s) already booked: {', '.join(sorted(clash))}", "error")
                else:
                    taken.update(seats)
                    bid = uuid.uuid4().hex[:8].upper()
                    BOOKINGS[bid] = {
                        "id": bid, "movie_id": movie_id, "movie": m["title"], "show": show,
                        "name": name, "email": email, "seats": sorted(seats),
                        "total": len(seats) * PRICE_PER_SEAT,
                        "time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                    }
                    return redirect(url_for("confirmation", booking_id=bid))

    booked = BOOKED.get((movie_id, show), set())
    return render_template("movie.html", movie=m, movie_id=movie_id, show=show,
                           rows=ROWS, per_row=SEATS_PER_ROW, booked=booked,
                           price=PRICE_PER_SEAT)


@app.route("/booking/<booking_id>")
def confirmation(booking_id):
    b = BOOKINGS.get(booking_id)
    if not b:
        abort(404)
    return render_template("confirmation.html", b=b)


@app.route("/bookings", methods=["GET", "POST"])
def bookings():
    results = None
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        results = [b for b in BOOKINGS.values() if b["email"].lower() == email]
    return render_template("bookings.html", results=results, email=email)


@app.route("/health")
def health():
    return {"status": "ok"}, 200


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
