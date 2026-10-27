from app.database.connection import get_connection


def main() -> None:
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            result = cursor.fetchone()

        print("Database connection successful!")
        print("-" * 50)
        print(result[0])

    finally:
        connection.close()


if __name__ == "__main__":
    main()