from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = "my-super-secret-key"

def get_db_connection():
    return mysql.connector.connect(
        host="185.114.247.43",
        port=3306,
        database="sch688_vvedenie",
        user="sch688_vvedenie",
        password="Qwerty123"
    )


@app.route("/")
def registration():
    return render_template("registration.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/user_register", methods=["POST"])
def user_register():
    req = request.get_json()

    name = req["name"]
    email = req["email"]
    password = req["password"]

    password_hash = generate_password_hash(password)

    cnx = get_db_connection()
    cur = cnx.cursor()

    cur.execute(
        """
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s)
        """,
        (name, email, password_hash)
    )

    cnx.commit()

    cur.close()
    cnx.close()

    return jsonify({
        "success": True,
        "message": "Пользователь зарегистрирован"
    })

@app.route("/user_login", methods=["POST"])
def user_login():
    req = request.get_json()

    email = req["email"]
    password = req["password"]

    cnx = get_db_connection()
    cur = cnx.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM users WHERE email = %s",
        (email,)
    )

    user = cur.fetchone()

    cur.close()
    cnx.close()

    if user is None:
        return jsonify({
            "success": False,
            "message": "Пользователь не найден"
        })

    if check_password_hash(user["password_hash"], password):
        session["user_email"] = user["email"]
        return jsonify({
            "success": True,
            "message": "Вход выполнен"
        })

    return jsonify({
        "success": False,
        "message": "Неверный пароль"
    })

@app.route("/profile")
def profile():

    if "user_email" not in session:
        return redirect("/login")

    email = session["user_email"]

    cnx = get_db_connection()
    cur = cnx.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM users WHERE email = %s",
        (email,)
    )

    user = cur.fetchone()

    cur.close()
    cnx.close()

    return render_template("profile.html", user=user)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)