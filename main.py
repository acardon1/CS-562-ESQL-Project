import sys
import subprocess
from importlib import util, import_module
import argparse

DATABASE_USERNAME = ""
DATABASE_PASSWORD = ""
DATABASE_SERVER = "localhost"
DATABASE_NAME = "postgres"

# Checks if the user has all the packages we are using installed and returns the module
def checkModule(mod_name):
    if util.find_spec(mod_name):
        print(f"{mod_name} already installed!")
    else:
        print(f"Installing {mod_name}")
        python = sys.executable
        subprocess.check_call([python, '-m', 'pip', 'install', mod_name], stdout=subprocess.DEVNULL)
        print(f"{mod_name} installed!")
    return import_module(mod_name)

# Establishes a connection to the database using psycopg2 and returns the values of the query
def commit_query(query,result):
    values = None
    connection = ""
    try:
        connection = psycopg2.connect(user= DATABASE_USERNAME,
                                    password= DATABASE_PASSWORD ,
                                    host= DATABASE_SERVER,
                                    database= DATABASE_NAME)
        cursor = connection.cursor()
        cursor.execute(query)
        if cursor.description != None: values = cursor.fetchall()
        connection.commit()
        print(result) 
        connection.close() 
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL: ", error)
        if(connection):
            connection.close() 
        exit()
    return values

# Run the file: python "e:/main.py" username password [optional] server_address database_name
# Example: python "e:/main.py" postgres pwd [localhost postgres]
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database Credentials")
    parser.add_argument("database_username", help="Database Authentication Username")
    parser.add_argument("database_password", help="Database Authentication Password")
    parser.add_argument("-s", "--server_address", help="Database Server Address")
    parser.add_argument("-d", "--database_name", help="Database Name")
    args = parser.parse_args()
    
    DATABASE_USERNAME = args.database_username
    DATABASE_PASSWORD = args.database_password
    
    if args.server_address:
        DATABASE_SERVER = args.server_address

    if args.database_name:
        DATABASE_NAME = args.database_name
     
    # Installs and imports the modules    
    psycopg2 = checkModule('psycopg2')
    np = checkModule('numpy')
    pd = checkModule('pandas')
    
    # Gets all the rows from the sales database by running the query below
    values = commit_query("""SELECT * from sales""", "Getting all entries in sales table")
    print(f"First Row of Sales Table: {values[0]}")
    print(f"Number of Rows: {len(values)}")
        
    
