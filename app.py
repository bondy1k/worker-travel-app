from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import csv
import sqlite3

app = Flask(__name__)

DB_PATH = "travel_app.db"


def init_db():
    """Create database tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_number TEXT,
            first_name TEXT,
            last_name TEXT,
            submitted_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS travel_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER,
            date TEXT,
            from_location TEXT,
            to_location TEXT,
            reason TEXT,
            travel_type TEXT,
            distance_km REAL,
            transportation_cost TEXT,
            parking REAL,
            meal_b INTEGER,
            meal_l INTEGER,
            meal_d INTEGER,
            escort INTEGER,
            receipt_file TEXT,
            FOREIGN KEY(submission_id) REFERENCES submissions(id)
        )
        """
    )
    conn.commit()
    conn.close()


def insert_submission(claim_number: str, first_name: str, last_name: str) -> int:
    """Insert a submission and return its DB id."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    submitted_at = datetime.now().isoformat()
    cur.execute(
        "INSERT INTO submissions (claim_number, first_name, last_name, submitted_at) VALUES (?, ?, ?, ?)",
        (claim_number, first_name, last_name, submitted_at),
    )
    submission_id = cur.lastrowid
    conn.commit()
    conn.close()
    return submission_id


def insert_travel_entry(submission_id: int, row: dict) -> None:
    """Insert a single travel entry linked to a submission."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO travel_entries (
            submission_id, date, from_location, to_location, reason,
            travel_type, distance_km, transportation_cost, parking,
            meal_b, meal_l, meal_d, escort, receipt_file
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            submission_id,
            row.get("date"),
            row.get("from"),
            row.get("to"),
            row.get("reason"),
            row.get("travel_type"),
            row.get("distance_km"),
            row.get("transportation_cost"),
            row.get("parking"),
            int(row.get("meal_b")),
            int(row.get("meal_l")),
            int(row.get("meal_d")),
            int(row.get("escort")),
            row.get("receipt_file"),
        ),
    )
    conn.commit()
    conn.close()


# Initialize the database when the application starts
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    # Create folders if they don't exist
    os.makedirs("submissions", exist_ok=True)
    os.makedirs("receipts", exist_ok=True)

    # Basic form fields
    claim_number = request.form.get("claim_number")
    last_name = request.form.get("last_name")
    first_name = request.form.get("first_name")

    # Detect how many travel rows there are
    row_count = 0
    for key in request.form.keys():
        if "date_" in key:
            row_num = int(key.split("_")[1])
            row_count = max(row_count, row_num)

    # Process each travel row
    travel_entries = []
    for i in range(1, row_count + 1):
        receipt_file = request.files.get(f"receipt_{i}")
        receipt_filename = None

        if receipt_file and receipt_file.filename != "":
            safe_name = secure_filename(receipt_file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            receipt_filename = f"{claim_number}_row{i}_{timestamp}_{safe_name}"
            receipt_file.save(os.path.join("receipts", receipt_filename))

        row = {
            "date": request.form.get(f"date_{i}"),
            "from": request.form.get(f"from_{i}"),
            "to": request.form.get(f"to_{i}"),
            "reason": request.form.get(f"reason_{i}"),
            "travel_type": request.form.get(f"travel_type_{i}"),
            "distance_km": request.form.get(f"km_{i}"),
            "transportation_cost": request.form.get(f"transportation_cost_{i}"),
            "parking": request.form.get(f"parking_{i}"),
            "meal_b": f"meal_b_{i}" in request.form,
            "meal_l": f"meal_l_{i}" in request.form,
            "meal_d": f"meal_d_{i}" in request.form,
            "escort": f"escort_{i}" in request.form,
            "receipt_file": receipt_filename
        }
        travel_entries.append(row)

    # Store submission in the database
    submission_id = insert_submission(claim_number, first_name, last_name)
    for row in travel_entries:
        insert_travel_entry(submission_id, row)

    # Final data package
    submission_data = {
        "claim_number": claim_number,
        "first_name": first_name,
        "last_name": last_name,
        "submitted_at": datetime.now().isoformat(),
        "travel_entries": travel_entries
    }

    # Save to JSON
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    json_path = os.path.join("submissions", f"{claim_number}_{timestamp}.json")
    with open(json_path, "w") as f:
        json.dump(submission_data, f, indent=4)

    # Save to CSV
    csv_path = os.path.join("submissions", f"{claim_number}_{timestamp}.csv")
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Date", "From", "To", "Reason", "Travel Type",
            "Distance (km)", "Transportation Cost", "Parking",
            "Meal B", "Meal L", "Meal D", "Escort", "Receipt File"
        ])
        for row in travel_entries:
            writer.writerow([
                row["date"], row["from"], row["to"], row["reason"],
                row["travel_type"], row["distance_km"], row["transportation_cost"],
                row["parking"], row["meal_b"], row["meal_l"], row["meal_d"],
                row["escort"], row["receipt_file"]
            ])

    # Render confirmation page
    return render_template("confirmation.html",
                           claim_number=claim_number,
                           first_name=first_name,
                           last_name=last_name,
                           row_count=len(travel_entries))


if __name__ == "__main__":
    app.run(debug=True)
