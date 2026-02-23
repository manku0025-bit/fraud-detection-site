
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import os
import sqlite3
import joblib
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
DB_FILE = "users.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Create table
with get_db() as db:
    db.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT UNIQUE,
        mobile TEXT,
        username TEXT,
        password TEXT
    )
    """)

# ---------------- LOAD ML MODELS ----------------
lr = joblib.load("models/model_lr.pkl")
rf = joblib.load("models/model_rf.pkl")
iso = joblib.load("models/model_if.pkl")

# ---------------- HELPER ----------------
def risk_level(score):
    if score <= 30:
        return "Low"
    elif score <= 60:
        return "Medium"
    else:
        return "High"

def encode(val):
    if isinstance(val, str):
        val = val.lower()
        if val in ["online","card","mobile","web","android"]:
            return 1
        else:
            return 0
    return val

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            flash("Password not match")
            return render_template("register.html")

        try:
            db = get_db()
            db.execute("INSERT INTO users(fullname,email,mobile,username,password) VALUES(?,?,?,?,?)",
                       (fullname,email,mobile,username,password))
            db.commit()
            flash("Registration success. Login now")
            return redirect("/login")
        except:
            flash("Email already registered")
            return render_template("register.html")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=? AND password=?",
                          (email,password)).fetchone()

        if user:
            session["user"] = user["fullname"]
            session["email"] = user["email"]
            return redirect("/dashboard")
        else:
            flash("Invalid email or password")

    return render_template("login.html")

# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot", methods=["GET","POST"])
def forgot():
    if request.method == "POST":
        email = request.form["email"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

        if not user:
            flash("Email not registered")
            return render_template("forgot.html")

        otp = str(random.randint(1000,9999))
        session["reset_otp"] = otp
        session["reset_email"] = email

        print("YOUR OTP IS:", otp)  # terminal OTP

        flash("OTP sent! Check terminal")
        return redirect("/reset")

    return render_template("forgot.html")

# ---------------- RESET PASSWORD ----------------
@app.route("/reset", methods=["GET","POST"])
def reset():
    if request.method == "POST":
        user_otp = request.form["otp"]
        new_pass = request.form["password"]

        if user_otp != session.get("reset_otp"):
            flash("Wrong OTP")
            return render_template("reset.html")

        db = get_db()
        db.execute("UPDATE users SET password=? WHERE email=?",
                   (new_pass, session.get("reset_email")))
        db.commit()

        flash("Password changed. Login now")
        return redirect("/login")

    return render_template("reset.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    results = []
    alert = False

    if request.method == "POST":
        file = request.files["file"]
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        df = pd.read_csv(path)

        for _, row in df.iterrows():
            amount = encode(row[0])
            ttype = encode(row[1]) if len(row) > 1 else 1
            device = encode(row[2]) if len(row) > 2 else 1

            features = [[amount, ttype, device]]

            p1 = lr.predict_proba(features)[0][1]*100
            p2 = rf.predict_proba(features)[0][1]*100
            p3 = 100 if iso.predict(features)[0] == -1 else 20

            score = round((p1+p2+p3)/3,2)
            risk = risk_level(score)

            if risk == "High":
                alert = True

            results.append({
                "Amount": amount,
                "Fraud_Status": "Fraud" if score>60 else "Safe",
                "Fraud_Score": score,
                "Risk_Level": risk
            })

        session["alerts"] = [r for r in results if r["Fraud_Status"]=="Fraud"]

    return render_template("dashboard.html",results=results,alert=alert)

# ---------------- ALERTS ----------------
@app.route("/alerts")
def alerts():
    if "user" not in session:
        return redirect("/login")
    return render_template("alerts.html",alerts=session.get("alerts",[]))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.debug = True
