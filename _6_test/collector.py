import pymysql
import requests

# 1. GitHub API 호출
url = "https://api.github.com"
response = requests.get(url)
data = response.json()

# 2. MySQL 연결
conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="admin",
    password="123456",
    database="github_db",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with conn.cursor() as cursor:
        # 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_endpoints (
                id INT AUTO_INCREMENT PRIMARY KEY,
                endpoint_name VARCHAR(100) NOT NULL,
                endpoint_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 기존 데이터 초기화 후 삽입
        cursor.execute("TRUNCATE TABLE github_endpoints")
        
        insert_query = "INSERT INTO github_endpoints (endpoint_name, endpoint_url) VALUES (%s, %s)"
        records = [(k, v) for k, v in data.items()]
        cursor.executemany(insert_query, records)

    conn.commit()
    print(f"총 {len(records)}개의 API 엔드포인트 데이터가 DB에 저장되었습니다.")

finally:
    conn.close()