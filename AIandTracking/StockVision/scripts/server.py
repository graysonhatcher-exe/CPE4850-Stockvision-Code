# Import Flask for creating the API server
from flask import Flask, jsonify, request

# Import Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, db

# Import datetime so we can timestamp updates
from datetime import datetime

# -----------------------------
# 1. Setup Flask
# -----------------------------
app = Flask(__name__)  # Create a Flask app instance

# -----------------------------
# 2. Setup Firebase
# -----------------------------
# Load your Firebase service account key (JSON file you downloaded from Firebase Console)
cred = credentials.Certificate("serviceAccountKey.json")

# Initialize Firebase app with your Realtime Database URL
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://test-d1cec-default-rtdb.firebaseio.com/'
})

# -----------------------------
# 3. API Endpoint: GET inventory
# -----------------------------
# This endpoint responds to GET requests at /inventory
# It returns the entire inventory in JSON format
@app.route("/inventory", methods=["GET"])
def get_inventory():
    ref = db.reference("inventory")  # Point to "inventory" node in Firebase
    data = ref.get()                 # Retrieve all inventory data
    return jsonify(data), 200        # Send it back as JSON with HTTP status 200 (OK)

# -----------------------------
# 4. API Endpoint: POST update
# -----------------------------
# This endpoint updates an item's quantity
# Example request:
# POST /update
# { "item": "soda", "change": 1 }
@app.route("/update", methods=["POST"])
def update_inventory():
    content = request.json  # Read JSON data from the request body

    # Extract fields from JSON
    item = content.get("item")           # Name of the item ("soda")
    change = int(content.get("change", 0))  # Change in quantity (+/-), default = 0

    # Get current quantity from Firebase (or 0 if it doesn't exist yet)
    ref = db.reference("inventory").child(item)
    current = ref.child("quantity").get() or 0

    # Calculate new quantity (don’t allow negative values)
    new_qty = max(current + change, 0)

    # Get current timestamp in a normal dd/mm/yyyy format
    timestamp = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

    # Update Firebase with new quantity and timestamp
    ref.update({
        "quantity": new_qty,
        "last_updated": timestamp
    })

    # Respond with confirmation message
    return jsonify({
        "message": f"{item} updated",
        "new_quantity": new_qty
    }), 200

# -----------------------------
# 5. Run Flask server
# -----------------------------
# This starts the server on http://127.0.0.1:5000
if __name__ == "__main__":
    app.run(debug=True)  # debug=True restarts the server on code changes