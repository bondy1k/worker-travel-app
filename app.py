from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import csv

app = Flask(__name__)

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
