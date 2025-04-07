from flask import Flask, request, jsonify
from db_config import get_db_connection
import os

app = Flask(__name__)

@app.route("/ping")
def ping():
    return "pong", 200

@app.route("/")
def index():
    return "Hello from Flask on Render!"


@app.route("/stocks", methods=["GET"])
def get_stocks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cardboard_stocks;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # レスポンスをわかりやすく整形
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "item": row[1],
            "quantity": row[2],
            "updated_at": row[3].isoformat()
        })
    return jsonify(result)


@app.route("/stocks", methods=["POST"])
def add_stock():
    data = request.json
    item = data.get("item")
    quantity = data.get("quantity")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO cardboard_stocks (item, quantity) VALUES (%s, %s);", (item, quantity))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Stock added"}), 201

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
