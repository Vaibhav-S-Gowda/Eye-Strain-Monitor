import psycopg2

conn = psycopg2.connect(

    database="eye_health_users",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432"

)

cursor = conn.cursor()


def create_users_table():

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS users(

        id SERIAL PRIMARY KEY,

        name TEXT,

        email TEXT,

        password TEXT

    )

    """)

    conn.commit()