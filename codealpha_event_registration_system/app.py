
from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            participant_name TEXT NOT NULL,
            email TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/events", methods=["GET"])
def get_events():
    conn = sqlite3.connect("events.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events ORDER BY id DESC")
    events = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify(events)


@app.route("/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    date = data.get("date", "").strip()
    location = data.get("location", "").strip()
    description = data.get("description", "").strip()

    if not name or not date or not location:
        return jsonify({
            "error": "Event name, date and location are required."
        }), 400

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events (name, date, location, description)
        VALUES (?, ?, ?, ?)
    """, (name, date, location, description))

    event_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Event created successfully!",
        "event_id": event_id
    }), 201


@app.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    conn = sqlite3.connect("events.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    conn.close()

    if event is None:
        return jsonify({"error": "Event not found."}), 404

    return jsonify(dict(event))


@app.route("/events/<int:event_id>/register", methods=["POST"])
def register_participant(event_id):
    data = request.get_json(silent=True) or {}

    name = data.get("participant_name", "").strip()
    email = data.get("email", "").strip()

    if not name or not email:
        return jsonify({
            "error": "Participant name and email are required."
        }), 400

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()

    if event is None:
        conn.close()
        return jsonify({"error": "Event not found."}), 404

    cursor.execute("""
        INSERT INTO registrations (event_id, participant_name, email)
        VALUES (?, ?, ?)
    """, (event_id, name, email))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Registration successful!",
        "event_id": event_id,
        "participant_name": name
    }), 201


@app.route("/events/<int:event_id>/registrations", methods=["GET"])
def get_registrations(event_id):
    conn = sqlite3.connect("events.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()

    if event is None:
        conn.close()
        return jsonify({"error": "Event not found."}), 404

    cursor.execute("""
        SELECT id, participant_name, email
        FROM registrations
        WHERE event_id = ?
        ORDER BY id DESC
    """, (event_id,))

    registrations = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(registrations)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)