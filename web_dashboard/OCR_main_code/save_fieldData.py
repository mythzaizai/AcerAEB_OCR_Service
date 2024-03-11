import os, uuid
import psycopg2

#PostgreSQL
#user:OCR_admin
#password: ej03xu3au4a83!



def setup_DBconnection():

    # Update connection string information
    host = "data-field-storage.postgres.database.azure.com" #<server-name>
    dbname = "postgres"                                     #<database-name>
    user = "OCR_admin"                                      #<admin-username>
    password = os.getenv("DB_password")              #<admin-password>
    sslmode = "require"

    # Construct connection string
    conn_string = "host={} user={} dbname={} password={} sslmode={}".format(host, user, dbname, password, sslmode)
    DBconnection = psycopg2.connect(conn_string)
    print("Connection established")

    return DBconnection



def test(DBconnection):

    DBcursor = DBconnection.cursor()

    # Drop previous table of same name if one exists
    DBcursor.execute("DROP TABLE IF EXISTS inventory;")
    print("Finished dropping table (if existed)")

    # Create a table
    DBcursor.execute("CREATE TABLE inventory (id serial PRIMARY KEY, name VARCHAR(50), quantity INTEGER);")
    print("Finished creating table")

    # Insert some data into the table
    DBcursor.execute("INSERT INTO inventory (name, quantity) VALUES (%s, %s);", ("cost", 990))

    print("Inserted data")


    # Fetch all rows from table

    DBcursor.execute("SELECT * FROM inventory;")
    rows = DBcursor.fetchall()

    # Print all rows

    for row in rows:
        print("Data row = (%s, %s, %s)" %(str(row[0]), str(row[1]), str(row[2])))



    # Clean up
    DBconnection.commit()
    DBcursor.close()
    DBconnection.close()


if __name__ == '__main__':

    print("[start]\n------------------\n")

    DBconnection = setup_DBconnection()

    test(DBconnection)

    print("\n------------------\n[processing end]")
