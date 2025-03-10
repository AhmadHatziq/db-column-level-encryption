import oracledb

un = 'test_user_1'
cs = 'localhost:1521/XE' # Check current session with 'SHOW CON_NAME;' If CDB$ROOT, set to XE.
pw = 'password'
with oracledb.connect(user=un, password=pw, dsn=cs) as connection:
    with connection.cursor() as cursor:
        sql = """select * from test_user_1.customer_table"""
        print(f"SQL command: {sql}")
        for r in cursor.execute(sql):
            print(r)