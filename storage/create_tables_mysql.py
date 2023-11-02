import mysql.connector
from mysql.connector import Error
import uuid

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='acit3855group45kafka.eastus2.cloudapp.azure.com', 
            user='user',  
            password='password'
        )
        print("Connection to MySQL DB successful")

        # Create a cursor object
        cursor = connection.cursor(dictionary=True)

        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS events")
        print("Database created successfully (if it didn't exist)")

        # Select the database
        cursor.execute("USE events")
        print("Database selected")

    except Error as e:
        print(f"The error '{e}' occurred")
        return None
    finally:
        if cursor:
            cursor.close()

    return connection

def create_table(connection, create_table_query):
    cursor = connection.cursor()
    try:
        cursor.execute(create_table_query)
        connection.commit()
        print("Table created successfully")
    except Error as e:
        print(f"The error '{e}' occurred")
    finally:
        cursor.close()

def main():
    connection = create_connection()

    create_carddb_table = """
    CREATE TABLE IF NOT EXISTS CardDB (
        card_id CHAR(36) NOT NULL,
        brand VARCHAR(255) DEFAULT NULL,
        `condition` VARCHAR(255) DEFAULT NULL,
        date_added DATETIME DEFAULT NULL,
        price INT DEFAULT NULL,
        seller_id VARCHAR(255) DEFAULT NULL,
        website VARCHAR(255) DEFAULT NULL,
        PRIMARY KEY (card_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """
# ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    create_sellerdb_table = """
    CREATE TABLE IF NOT EXISTS SellerDB (
        rating_id CHAR(36) NOT NULL,
        seller_id VARCHAR(255) NOT NULL,
        user_id VARCHAR(255) NOT NULL,
        rating INT NOT NULL,
        comment VARCHAR(1024) DEFAULT NULL,
        date_rated DATETIME NOT NULL,
        PRIMARY KEY (rating_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    if connection is not None:
        create_table(connection, create_carddb_table)
        create_table(connection, create_sellerdb_table)
        connection.close()
    else:
        print("Failed to create database connection.")

if __name__ == "__main__":
    main()
