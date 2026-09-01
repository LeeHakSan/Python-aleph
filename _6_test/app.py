import csv
import io
import json
import pymysql
from flask import Flask, Response, make_response, render_template_string

app = Flask(__name__)

def get_db_connection():
    return pymysql.connect(
        host="localhost",
        port=3306,
        user="admin",
        password="123456",
        database="github_db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>GitHub API Endpoints</title>
    <style>
        body { font-family: sans-serif; margin: 30px; }
        table { border-collapse: collapse; width: 100%; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .btn { padding: 8px 12px; text-decoration: none; background: #007bff; color: white; border-radius: 4px; margin-right: 5px; }
        .btn-green { background: #28a745; }
    </style>
</head>
<body>
    <h2>GitHub API Endpoints DB List</h2>
    <a href="/export/csv" class="btn">CSV 파일 다운로드</a>
    <a href="/export/json" class="btn btn-green">JSON 파일 다운로드</a>
    
    <table>
        <tr>
            <th>ID</th>
            <th>Endpoint Name</th>
            <th>URL</th>
            <th>Saved At</th>
        </tr>
        {% for row in rows %}
        <tr>
            <td>{{ row.id }}</td>
            <td><strong>{{ row.endpoint_name }}</strong></td>
            <td><a href="{{ row.endpoint_url }}" target="_blank">{{ row.endpoint_url }}</a></td>
            <td>{{ row.created_at }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# 메인 웹 페이지
@app.route("/")
def index():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM github_endpoints ORDER BY id ASC")
        rows = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, rows=rows)

# CSV 다운로드 라우트
@app.route("/export/csv")
def export_csv():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, endpoint_name, endpoint_url, created_at FROM github_endpoints")
        rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "endpoint_name", "endpoint_url", "created_at"])
    for r in rows:
        writer.writerow([r["id"], r["endpoint_name"], r["endpoint_url"], str(r["created_at"])])

    response = Response(output.getvalue().encode("utf-8-sig"), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=github_endpoints.csv"
    return response

# JSON 다운로드 라우트
@app.route("/export/json")
def export_json():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, endpoint_name, endpoint_url, created_at FROM github_endpoints")
        rows = cursor.fetchall()
    conn.close()

    json_str = json.dumps(rows, default=str, ensure_ascii=False, indent=2)
    response = Response(json_str, mimetype="application/json")
    response.headers["Content-Disposition"] = "attachment; filename=github_endpoints.json"
    return response

if __name__ == "__main__":
    app.run(debug=True, port=5000)