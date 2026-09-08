import psycopg2

try:
    connection = psycopg2.connect(
        host="localhost",
        port="5432",
        database="market_data",
        user="postgres",
        password="etl_password"
    )
    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    
    print("🚀 Successfully connected to PostgreSQL!")
    print(f"Database version: {db_version[0]}")

    cursor.close()
    connection.close()

except Exception as error:
    print(f"❌ Connection failed: {error}")