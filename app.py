from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    # Grab form fields
    last_name = request.form.get("last_name")
    first_name = request.form.get("first_name")
    claim_number = request.form.get("claim_number")
    km = request.form.get("km_1")
    taxi_amount = request.form.get("taxi_1")
    parking = request.form.get("parking_1")
    
    # Print to terminal for testing
    print("Form submitted!")
    print(f"Name: {first_name} {last_name}")
    print(f"Claim #: {claim_number}")
    print(f"Distance: {km} km, Taxi: ${taxi_amount}, Parking: ${parking}")

    return "Form submitted successfully!"

if __name__ == "__main__":
    app.run(debug=True)
