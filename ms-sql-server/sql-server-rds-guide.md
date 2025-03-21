# Demo Guide of SQL Server Always Encrypted on AWS RDS 

SQL Server Always Encrypted documentation - https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-database-engine?view=sql-server-ver16

## 1. Purpose 
The purpose of this guide is to demonstrate how to enable Field Level Encryption in SQL Server on AWS RDS.

Field Level encryption is enabled via SQL Server's Always Encrypt (AE) feature.

This guide will demonstrate the process to setup a table with column-level encryption (via the AE feature) and illustrate the process of how this protects the columns from unauthorized users.

For the latest updates, please refer to Microsoft's official documentation on the AE feature:
- Tutorial on Starting with Always Encrypt - https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-tutorial-getting-started?view=sql-server-ver16&tabs=ssms
- Introduction to SQL Server Always Encrypt - https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-database-engine
- Developer guide on SQL Server Always Encrypt - https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-client-development
- AWS guide on using SQL Server Always Encrypt on RDS - https://aws.amazon.com/blogs/database/set-up-always-encrypted-with-amazon-rds-for-sql-server/

## 2. Background
![Always Encrypt Flow](../img/sql_server_always_enc_flow.png)

Terminology: 

- CMK - Column Master Key
- CEK - Column Encryption Key
- `pfx` certification - X.509 cert containing public, private keys and CRL 

Always Encrypted is a client-side encryption technology that ensures sensitive data (and related encryption keys) are never revealed to the SQL Server Database. The certificates, CMK and CEK are not stored on the SQL Server. Only references are stored.

With Always Encrypted, a client driver transparently encrypts sensitive data before passing the data to the Database Engine, and it transparently decrypts data retrieved from encrypted database columns.

The CMK involves the use of a `pfx` file. SSMS can generate the pfx certificate locally. 

To share access to the encrypted columns, sharing of the pfx certificate to authorized users is required, as well as the passowrd used to protect the pfx file. 

The certificate used can be chosen to be from the local store (local to your machine, not local to SQL Server). 

You can access the windows local cert store with: 
`WINDOWS_Key + R` => `certmgr.msc` => Personal => Certificates

All decryption and encryption operations (including certs) happen at the client side. Nothing is stored at the DB, except for references to the CMK and the encrypted CEK etc. 

![How AE Works](../img/always-encrypted-how-queries-against-encrypted-columns-work.png)

### Elaboration on cryptography used 
A .pfx  certificate consists of components such as the private key, public key and CRLs. References below:
- https://learn.microsoft.com/en-us/windows-hardware/drivers/install/personal-information-exchange---pfx--files
- https://www.advancedinstaller.com/what-is-pfx-certificate.html

The private key in the pfx  certificate is used as the Column Master Key (CMK). 

CMK is used to encrypt CEKs by using asymmetric RSA with Optimal Asymmetric Encryption Padding (RSA-OAEP)

CEKs are used to encrypt the sensitive columns via symmetric encryption. 

*Storage*

CEKs are encrypted and stored on the database. Only the CMK can be used to access the encrypted CEKs. 

CMKs are not stored on the database. They are only stored in the trusted key store, such as the pfx  cert in the Windows Certificate Store. 

Only the CMK metadata is stored on the database. 
Protecting the CMK

As the CMK is stored in the pfx  file, we are required to specify a password to protect it, when exporting the CMK. 

The pfx  cert file (along with the password) should be stored securely, such as on AWS Secrets Manager. 

For a thorough understanding, please refer to the following Microsoft documentation: 

Key Management in AE: https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/overview-of-key-management-for-always-encrypted
Cryptography in AE: https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-cryptography

## 3. Pre-requisites 
- RDS Instance running SQL Server
- SQL Server Management Studio (SSMS) to connect to the RDS SQL Server instance
- DB admin permissions
- Access to Windows Local User Certificate Store

Below is the RDS SQL Server settings that this demo was created on: 

![RDS SQL Server Settings](../img/rds_sql_server_config.png)

## 4. Create SQL Server instance on RDS. Alter Security Group rules to allow connection via MS SQL. 

Use https://whatismyipaddress.com/ to find out own IP address and add into security group. 

![RDS Security Group Rules](../img/rds_security_group_rules.png)

## 5. Connect to SQL instance using SSMS. (with DB admin account)

## 6. Create a new test DB. Eg `test-db-1`

## 7. Creating Certificate (Optional) and CMK
To create the CMK, we need to select the required cert. 
The Certificates can be viewed when creating the CMK. 

![Create CMK](../img/sql_server_generate_cmk_1.png)

![Create CMK & View Certs](../img/sql_server_generate_cmk_view_certs.png)

If we generate a new certificate (on `Windows Certificate Store – Current User`), this certificate is created locally, not on the DB. 

When you create a Column Master Key (CMK) using a certificate from the `Windows Certificate Store – Current User`, the actual certificate is not stored on the SQL Server. Instead, only a reference to that certificate (and the associated metadata) is stored in the database. The certificate remains securely in the Windows Certificate Store on your client machine. This design helps ensure that the private key used for encryption remains under your control and is not directly exposed on the server side.

To view the certs stored locally, use `WINDOWS_Key + R` => `certmgr.msc` => Personal => Certificates

![Windows Cert Store](../img/windows_cert_store.png)

## 8. Export the cert used for the CMK. 

The cert used is created locally (not on SQL Server). We would need to export the cert for other users to access the key and for safekeeping. It is recommended to store the cert in a safe location for sharing, such as Secrets Manager. 

We can access it as follows: 

![Create CMK & View Certs](../img/sql_server_export_cert.png)

In the CMK creation screen, double click the certificate used. 

![Export Cert 2](../img/sql_server_export_cert_2.png)

![Export Cert 3](../img/sql_server_export_cert_3.png)

Navigate to `Details` => `Copy to File`. Save the file somewhere. Input a passphrase if required. 

An alternate way to export the key is via the Windows Cert Store. 
Use `WINDOWS_Key + R` => `certmgr.msc` => Personal => Certificates

![Windows Cert Store](../img/windows_cert_store.png)

To allow other users to have access to the CMK and CEK (and subsequently the Always Encrypted sensitive column), they will need to install this cert and reference this when connecting to SQL Server. 

Note that in this example, we are using `Windows Certificate Store - Current User`. This is the personal store of the connected admin user. 

The cert/CMK is never stored on the Database. 

![MS Docs 1](../img/sql_server_ms_docs_1.png)

The above screenshot from Microsoft docs indicates that the `Certificate Store - Current User` is local to the client machine, not on the DB. 

Reference: 

- Microsoft guide on provisioning CMK and CEK - https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/configure-always-encrypted-keys-using-ssms?view=sql-server-ver16

![Cert Export 1](../img/export_cert_1.png)

![Cert Export 2](../img/export_cert_2.png)

![Cert Export 3](../img/export_cert_3.png)

![Cert Export 4](../img/export_cert_4.png)

When exporting the cert, as it contains the private CMK, please specify a strong password. 

## 9. Create the CEK. 

Similar to the CMK, use the GUI to create a CEK. The CEK requires access to the previously created CMK. 

![Create CEK](../img/sql_server_generate_cek_1.png)

## 10. Create the encrypted table. 

For this demo, we will create a table of customer data. The credit card information will be encrypted using Always Encrypted. 

Create Table Command: 
```
USE [test-db-1]
CREATE TABLE CustomerInfo (
    CustomerID INT NOT NULL PRIMARY KEY, 
    CustomerName NVARCHAR(50) NOT NULL, 
    CustomerCreditCard INT ENCRYPTED WITH (
        ENCRYPTION_TYPE = Deterministic, 
        ALGORITHM = 'AEAD_AES_256_CBC_HMAC_SHA_256', 
        COLUMN_ENCRYPTION_KEY = CEK_1
    ) NOT NULL
)
```

![Create Table](../img/sql_server_create_table.png)

## 11. Enable Always Encrypt settings in SSMS 

Before we can interact with the Always Encrypt (AE) column, we need to configure SSMS first. 

Go to SSMS Options > Query Execution > Advanced > Enable Parameterization for Always Encrypted 

![Configure SSMS Parameterization](../img/sql_server_ae_settings_1.png)

Reconnect back to SQL Server instance and enable AE 

![Configure SQL Server Connection](../img/sql_server_ae_settings_2.png)

## 12. Insert data into the table 

Note that due to how encryption is done at the client-side in Always Encrypted, normal INSERT statements will have to be parameterized. 

For more details, please refer to the Microsoft documentation [here](https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-how-queries-against-encrypted-columns-work?view=sql-server-ver16) 

The below INSERT command will FAIL: 
```
INSERT INTO CustomerInfo (CustomerID, CustomerName, CustomerCreditCard)
VALUES (1, 'Alice Johnson', 123);

```

The below INSERT command will work: 
```
DECLARE @id INT = 21
DECLARE @name NVARCHAR(50) = 'Kalle'
DECLARE @card INT = 45
insert into CustomerInfo (CustomerID, CustomerName, CustomerCreditCard) 
VALUES (@id, @name, @card)

```

![Insert Success](../img/sql_server_insert_success.png)

If we query the column, we will be able to see the encrypted data easily. 
This is as our current account has access to the certificates used to create the CMK and CEK. 

## 13. Create a new role and verify that data is encrypted 
### 13.1 Create a new role 

Use the following commands to create a new DB role (username `user-1` with password `user-1`): 
```
USE [master];
GO

--Create a server-level login 
CREATE LOGIN [user-1] WITH PASSWORD = 'user-1';
GO

--Set context to msdb database
USE [test-db-1];
GO

--Create a database user & link it to server-level login theirname
CREATE USER [user-1] FOR LOGIN [user-1];
GO

-- Grant permissions to select on table 
USE [test-db-1];
GRANT SELECT ON [dbo].[CustomerInfo] TO [user-1];

```

In this example, we will be using Python and ODBC drivers to access the encrypted column. 

### 13.2 Remove the certificate from the Windows Cert Store 

Windows machine is assumed to be used. 

Access the windows cert store with: 
`WINDOWS_Key + R`, `certmgr.msc`

![Access Windows Cert Store](../img/windows_cert_store_command.png)

Delete all certs relating to Always Encrypted: 
- Note that these certs were present as we used the same machine to configure the DB and create the CMK / CEK previously. 

![Delete AE Certs](../img/windows_delete_certs.png)

### 13.3 Run Python, configure to connect as the new user without certs installed

Python ODBC uses a connection string to authenticate and access the AE columns. 
In this demo, the connection string will use any certs installed in the Local Windows Cert Store. 
As we have removed the certs, this user will not be able to view the encrypted columns programmatically. 

Note: Python code works in Windows, but not WSL. Need to explore how to import certs into Linux. 

The below Python code is used to test this connection: 
```
import pyodbc 
connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=<INSERT-RDS-ENDPOINT>,1433;"
    "DATABASE=test-db-1;"
    "UID=user-1;"
    "PWD=user-1;"
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
    
    # Query data from table with enc info
    cursor.execute("SELECT * FROM [test-db-1].[dbo].[CustomerInfo]")
    rows = cursor.fetchall()
    for row in rows:
        print(str(row))

except pyodbc.Error as e:
    print("Error connecting to SQL Server:", e)

finally:
    # Close the connection
    if connection:
        connection.close()
```

Output: 

```
D:\Documents\playground\always_enc_sql_server>python code.py
Attempting to connect to local SQL SERVER DB.
Connection successful!
Connectiong string: DRIVER={ODBC Driver 18 for SQL Server};SERVER=<RDS-ENDPOINT>,1433;DATABASE=test-db-1;UID=user-1;PWD=user-1;Encrypt=yes;TrustServerCertificate=yes;ColumnEncryption=Enabled;KeyStoreAuthentication=WindowsCertificateStore;
Error connecting to SQL Server: ('CE027', "[CE027] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Certificate in key path 'CurrentUser/My/D150F461220871288DD7E0ACADADE69D45FDC776' not found. (0) (SQLGetData); [CE027] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]The keystore provider MSSQL_CERTIFICATE_STORE failed to decrypt the ECEK CurrentUser/My/D150F461220871288DD7E0ACADADE69D45FDC776 with RSA_OAEP. (0)")
```

![Python Cannot Access](../img/sql_server_python_fail.png)

As expected, access to the column is denied. 
However, if we only SELECT the non-encrypted column (`SELECT CustomerName  FROM [test-db-1].[dbo].[CustomerInfo]`), this will work. 

![Python Access Unencrypted Column](../img/sql_server_python_access_non_ae_cols.png)

### 13.4 Install the certs and execute again 

Using the previously exported cert, import it into the system. 
As we are using Windows, just double click the cert, which will trigger the Certificate Import Wizard. 

![Import Cert 1](../img/windows_import_cert_1.png)

![Import Cert 2](../img/windows_import_cert_2.png)

![Import Cert 3](../img/import_cert_1.png)
- Specify the password used when exporting the cert file. 

Once imported, we can verify in Windows Certificate Manager that the cert is present (refresh if needed)

![Import Cert 3](../img/windows_import_cert_3.png)

This will ensure that the user has access to the CMK and can decrypt the CEK and subsequent AE columns. 

Execute the Python code again. 

Now, the new user `user-1` is able to view the encrypted column. 
The credit card information is shown (the last column). 

![Python Success](../img/sql_server_python_success.png)

This example shows that to delegate access of the encrypted column to other users, installation of the Certificate (used to create the CMK) is needed. 

## 14. Can another DB admin access the certs/keys created by the first DB admin? 

No. All encryption/decryption operations happens client side. 

When a DBA first creates a CMK, the cert is generated on his/her client machine. 

For other users to access the encrypted data, the DBA will need to share this cert with them, as long as the password used to protect the cert. 

For more details, please refer to Microsoft docs: https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-how-queries-against-encrypted-columns-work?view=sql-server-ver16


## 15. Certificate Rotation 

Relevant documentation: 
- Always Encrypted Key Rotation with SSMS - https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/rotate-always-encrypted-keys-using-ssms?view=sql-server-ver16
- Overview of Keys in Always Encrypted - https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/overview-of-key-management-for-always-encrypted?view=sql-server-ver16

To rotate a CMK, we need to create another CMK first (preferably using another certificate). 

In this example, we have another CMK called `test cmk 1`. We will rotate the old CMK `Master Key from Auto Cert 1` with the new CMK `test cmk 1`. 

![Rotate CMK 1](../img/sql_server_rotate_key_1.png)

![Rotate CMK 2](../img/sql_server_rotate_key_2.png)

Once rotation is done, please update all clients to use the latest certificate. 

After this is done, we can perform cleanup of the old CMK. 

![Cleanup CMK 1](../img/sql_server_cleanup_key_1.png)

![Cleanup CMK 2](../img/sql_server_cleanup_key_2.png)

For a more thorough guide on rotating the certs and keys, please visit Microsoft's official documentation above. 

