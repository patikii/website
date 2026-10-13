from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os
from dotenv import load_dotenv
import requests
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
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
        session["balance"] = 1000

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

    fullname = user["username"].split(" ", 1)

    name = fullname[0]

    if len(fullname) > 1:
        surname = fullname[1]
    else:
        surname = ""

    return render_template(
        "profile.html",
        user=user,
        name=name,
        surname=surname,
        balance=session["balance"]
    )

@app.route("/give_money", methods=["POST"])
def give_money():
    if "user_email" not in session:
        return redirect("/login")

    if session["balance"] >= 100:
        session["balance"] -= 100

    return redirect("/profile")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/ask_ai", methods=["POST"])
def ask_ai():
    if "user_email" not in session:
        return jsonify({
            "success": False,
            "answer": "Сначала войдите в аккаунт"
        })

    req = request.get_json()
    question = req["question"]

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        },
        timeout=30
    )

    data = response.json()

    answer = data["choices"][0]["message"]["content"]

    return jsonify({
        "success": True,
        "answer": answer
    })

if __name__ == "__main__":
    app.run(debug=True)