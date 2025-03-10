import pyodbc 

print("Attempting to connect to local SQL SERVER DB.")

# Define the connection string

# Below connection string cannot be used for accesing the columns
'''
connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;"
    "Encrypt=no;"
    "DATABASE=master;"
    "UID=SA;"
    "PWD=Sample123$;"
    "ColumnEncryption=Enabled;"
)
'''

# Below connection string works for WindowsCertStore auth ie cert installed via WindowsCertStore 
connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=10.255.255.254,1433;"
    "DATABASE=master;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "ColumnEncryption=Enabled;"
    "KeyStoreAuthentication=WindowsCertificateStore;"
)

# Establish the connection
try:
    connection = pyodbc.connect(connection_string)
    print("Connection successful!")
    print(f"Connectiong string: {str(connection_string)}")

    # Create a cursor object to interact with the database
    cursor = connection.cursor()
    
    # Query to view tables
    cursor.execute("SELECT * FROM [master].[dbo].[CustomerInfo]")
    
    # Fetch and print all table names
    tables = cursor.fetchall()
    for table in tables:
        print(table[0])

except pyodbc.Error as e:
    print("Error connecting to SQL Server:", e)

finally:
    # Close the connection
    if connection:
        connection.close()
