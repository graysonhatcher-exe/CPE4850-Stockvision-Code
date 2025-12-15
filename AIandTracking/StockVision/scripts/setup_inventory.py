import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Setup Firebase (you already have this in your main.py)
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://test-d1cec-default-rtdb.firebaseio.com/'
})

# Define initial inventory (just names, quantity, and last updated time)
initial_inventory = {
    "Granola Bar": {"quantity": 0, "last_updated": str(datetime.now())},
    "Butter Finger": {"quantity": 0, "last_updated": str(datetime.now())},
    "Doritos": {"Doritos": 0, "last_updated": str(datetime.now())},
    "Gummy": {"Gummy": 0, "last_updated": str(datetime.now())}
}

# Push to database
ref = db.reference("inventory")
ref.set(initial_inventory)

print("✅ Inventory database initialized!")