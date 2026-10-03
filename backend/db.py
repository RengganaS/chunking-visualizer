import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Established and returns a connection to the database."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

if __name__ == "__main__":
    connection = get_db_connection()
    if connection:
        print("Successfully connected to the database!")

        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT current_database();")
            current_db = cursor.fetchone()
            print(f"Successfully connected to database: '{current_db['current_database']}'")
            
            cursor.execute("""
                SELECT table_name
                from information_schema.tables
                WHERE table_schema = 'public';
            """)
            tables = cursor.fetchall()
            print("Found tables:", [t['table_name'] for t in tables])

        connection.close()
