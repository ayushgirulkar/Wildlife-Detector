from flask import Flask, render_template, request, redirect, session
from flask_cors import CORS
from ultralytics import YOLO
import mysql.connector
import os
import cv2

app = Flask(__name__)
app.secret_key = 'secret'
CORS(app)

# Load YOLO model
model = YOLO('model/best.pt')

# MySQL DB connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123",  # Replace with your actual MySQL password
    database="wildlife_db"
)
cursor = db.cursor()

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Routes ---

@app.route('/')
def login():
    return render_template("login.html")

@app.route('/login', methods=["POST"])
def do_login():
    username = request.form['username']
    password = request.form['password']
    cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
    admin = cursor.fetchone()
    if admin:
        session['admin'] = username
        return redirect('/dashboard')
    else:
        return "Invalid login"

@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/')

    # Explicitly select necessary columns in correct order
    cursor.execute("SELECT id, label, location, latitude, longitude, time FROM alerts ORDER BY time DESC")
    alerts = cursor.fetchall()
    
    return render_template("dashboard.html", alerts=alerts)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'admin' not in session:
        return redirect('/')

    if request.method == 'POST':
        file = request.files['media']
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Get location from form
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)

        # Fallback to India if location not provided
        if latitude is None or longitude is None:
            latitude, longitude = 20.5937, 78.9629

        # YOLO detection
        if filename.lower().endswith(('.mp4', '.avi', '.mov')):
            results = model(filepath)
        elif filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            img = cv2.imread(filepath)
            results = model(img)
        else:
            return "Unsupported file format", 400

        # --- Detect labels ---
        labels_detected = set()
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                label = model.names[class_id]
                labels_detected.add(label)

        # --- Decide which alerts to insert ---
        insert_alerts = set()

        if 'fire' in labels_detected:
            insert_alerts.add("fire")

        if 'person' in labels_detected and 'elephant' in labels_detected:
            insert_alerts.add("hunting")
        else:
            if 'person' in labels_detected:
                insert_alerts.add("person")
            if 'elephant' in labels_detected:
                insert_alerts.add("elephant")

        # --- Insert all alerts using SAME location ---
        for label in insert_alerts:
            cursor.execute(
                "INSERT INTO alerts (label, location, latitude, longitude) VALUES (%s, %s, %s, %s)",
                (label, "Device Upload", latitude, longitude)
            )

        db.commit()

        return redirect('/dashboard')

    return render_template("upload.html")

@app.route('/clear_alerts', methods=['POST'])
def clear_alerts():
    if 'admin' not in session:
        return redirect('/')
    cursor.execute("DELETE FROM alerts")
    db.commit()
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True)
