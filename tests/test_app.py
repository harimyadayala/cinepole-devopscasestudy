import app as appmod


def client():
    appmod.BOOKED.clear()
    appmod.BOOKINGS.clear()
    appmod.app.config["TESTING"] = True
    return appmod.app.test_client()


def test_home_page():
    r = client().get("/")
    assert r.status_code == 200 and b"Now Showing" in r.data


def test_health():
    assert client().get("/health").get_json() == {"status": "ok"}


def test_movie_page():
    assert b"Galaxy Runners" in client().get("/movie/1").data


def test_unknown_movie_404():
    assert client().get("/movie/99").status_code == 404


def test_booking_and_double_booking_blocked():
    c = client()
    data = {"name": "Asha", "email": "asha@x.com", "show": "10:00 AM", "seats": ["A1", "A2"]}
    r = c.post("/movie/1", data=data)
    assert r.status_code == 302
    r2 = c.post("/movie/1", data=data, follow_redirects=True)
    assert b"already booked" in r2.data


def test_my_bookings_lookup():
    c = client()
    c.post("/movie/2", data={"name": "Ravi", "email": "r@x.com", "show": "11:00 AM", "seats": ["B3"]})
    r = c.post("/bookings", data={"email": "r@x.com"})
    assert b"Monsoon Melody" in r.data
