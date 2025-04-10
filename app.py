from flask import Flask, request, jsonify
from db_config import get_db_connection
import os
from flask import Flask, request, jsonify, render_template
from datetime import datetime
from flask import send_file
from pytz import timezone
import csv
import io
import psycopg2

app = Flask(__name__)

# 登録画面を返すルート
@app.route("/cardboard-types-ui")
def cardboard_types_ui():
    return render_template("cardboard_types.html")

# 種類一覧取得
@app.route("/api/cardboard-types", methods=["GET"])
def get_cardboard_types():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cardboard_types ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "name": row[1],
            "size": row[2],
            "notes": row[3]
        })
    return jsonify(result)

# 登録 or 更新（idがあれば更新）
@app.route("/api/cardboard-types", methods=["POST"])
def add_or_update_cardboard_type():
    data = request.json
    id = data.get("id")
    name = data.get("name")
    size = data.get("size")
    notes = data.get("notes")

    conn = get_db_connection()
    cur = conn.cursor()
    if id:
        cur.execute("UPDATE cardboard_types SET name=%s, size=%s, notes=%s WHERE id=%s",
                    (name, size, notes, id))
    else:
        cur.execute("INSERT INTO cardboard_types (name, size, notes) VALUES (%s, %s, %s)",
                    (name, size, notes))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "OK"})

# 削除
@app.route("/api/cardboard-types/<int:id>", methods=["DELETE"])
def delete_cardboard_type(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cardboard_types WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "deleted"})

# 📦 入荷予約を登録（POST）
@app.route("/api/arrivals", methods=["POST"])
def create_arrival():
    data = request.json
    cardboard_type_id = data.get("cardboard_type_id")
    quantity = data.get("quantity")
    scheduled_date = data.get("scheduled_date")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO cardboard_arrivals (cardboard_type_id, quantity, scheduled_date)
        VALUES (%s, %s, %s)
    """, (cardboard_type_id, quantity, scheduled_date))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "予約完了"})

# 📋 予約一覧（未入荷のみ）
@app.route("/api/arrivals", methods=["GET"])
def get_arrivals():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, c.name, a.quantity, a.scheduled_date, a.is_arrived
        FROM cardboard_arrivals a
        JOIN cardboard_types c ON a.cardboard_type_id = c.id
        WHERE a.is_arrived = FALSE
        ORDER BY a.scheduled_date
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "name": row[1],
            "quantity": row[2],
            "scheduled_date": row[3].isoformat(),
            "is_arrived": row[4]
        })
    return jsonify(result)

# ✅ 入荷完了（在庫へ反映）
@app.route("/api/arrivals/<int:id>/confirm", methods=["POST"])
def confirm_arrival(id):
    conn = get_db_connection()
    cur = conn.cursor()

    # 該当予約を取得
    cur.execute("SELECT cardboard_type_id, quantity FROM cardboard_arrivals WHERE id=%s", (id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "予約が見つかりません"}), 404
    cardboard_type_id, quantity = row

    # 在庫テーブルに加算 or 挿入
    cur.execute("SELECT quantity FROM cardboard_stock WHERE cardboard_type_id=%s", (cardboard_type_id,))
    stock = cur.fetchone()
    if stock:
        new_qty = stock[0] + quantity
        cur.execute("UPDATE cardboard_stock SET quantity=%s WHERE cardboard_type_id=%s", (new_qty, cardboard_type_id))
    else:
        cur.execute("INSERT INTO cardboard_stock (cardboard_type_id, quantity) VALUES (%s, %s)", (cardboard_type_id, quantity))

    # 予約フラグ更新
    cur.execute("UPDATE cardboard_arrivals SET is_arrived=TRUE WHERE id=%s", (id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "入荷完了・在庫更新済み"})

# 在庫一覧取得
@app.route("/api/stocks", methods=["GET"])
def get_stocks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT s.id, c.name, c.size, c.notes, s.quantity
    FROM cardboard_stock s
    JOIN cardboard_types c ON s.cardboard_type_id = c.id
    ORDER BY c.name
""")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "stock_id": row[0],
            "name": row[1],
            "size": row[2],
            "notes": row[3],        # ← ここが必須！
            "quantity": row[4]
        })
    return jsonify(result)

# 任意の数量で在庫更新（増加 or 減少）
@app.route("/api/stocks/<int:stock_id>/adjust", methods=["POST"])
def adjust_stock(stock_id):
    data = request.json
    amount = int(data.get("amount", 0))  # 例: -5 や +3

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE cardboard_stock SET quantity = GREATEST(quantity + %s, 0) WHERE id = %s", (amount, stock_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": f"数量調整 {amount:+d}"})

@app.route("/cardboard-stock-ui")
def cardboard_stock_ui():
    return render_template("cardboard_stock.html")


@app.route('/download-logs')
def download_logs():
    # DB接続
    conn = get_db_connection()
    cursor = conn.cursor()

    # データ取得（JOINして名前付き）
    cursor.execute("""
        SELECT
            logs.id,
            logs.operated_at,
            logs.operation,
            logs.cardboard_type_id,
            types.name AS cardboard_name,
            logs.quantity_change,
            logs.operator,
            logs.comment
        FROM stock_operation_logs logs
        JOIN cardboard_types types ON logs.cardboard_type_id = types.id
        ORDER BY logs.operated_at DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

# JSTタイムゾーン
    jst = timezone('Asia/Tokyo')

    # CSV書き込み
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '操作日時', '操作', '段ボールID', '段ボール名', '数量変化', '操作ユーザー', 'コメント'])
    for row in rows:
        operated_at_utc = row[1]
        operated_at_jst = operated_at_utc.astimezone(jst)
        writer.writerow([
            row[0],
            operated_at_jst.strftime('%Y-%m-%d %H:%M:%S'),
            row[2], row[3], row[4], row[5], row[6], row[7]
        ])

    output.seek(0)
    filename = f"stock_operation_logs_{datetime.now(jst).strftime('%Y%m%d')}.csv"

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route("/ping")
def ping():
    return "pong", 200

@app.route("/")
def index():
    return "Hello from Flask on Render!"

@app.route("/cardboard-arrivals-ui")
def cardboard_arrivals_ui():
    return render_template("cardboard_arrivals.html")



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
