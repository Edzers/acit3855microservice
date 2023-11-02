import mysql.connector
from mysql.connector import Error

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='acit3855group45kafka.eastus2.cloudapp.azure.com', 
            user='user',  # the username from your docker-compose file
            password='password',  # the password from your docker-compose file
            database='events'  # the database name from your docker-compose file
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
        return None

    return connection

def drop_table(connection, table_name):
    cursor = connection.cursor()
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        connection.commit()
        print(f"Table '{table_name}' dropped successfully")
    except Error as e:
        print(f"The error '{e}' occurred")
    finally:
        cursor.close()

def main():
    connection = create_connection()

    if connection is not None:
        drop_table(connection, 'CardDB')  
        drop_table(connection, 'SellerDB')  
        connection.close()
    else:
        print("Failed to create database connection.")

if __name__ == "__main__":
    main()
