filename: jtds.jar
driver: net.sourceforge.jtds.jdbc.Driver
source: http://jtds.sourceforge.net

example usage:

import jaydebeapi
conn = jaydebeapi.connect("net.sourceforge.jtds.jdbc.Driver",
                              "jdbc:jtds:sybase://t016100.lewis.co.za:5000;DatabaseName=REDLEWIS",
                              ["lewis", "redpassword"],
                              "/app/Refresher/jtds.jar",)
curs = conn.cursor()
curs.execute("select * from branch_control")
print(curs.fetchall())
curs.close()
conn.close()

other

>>> import jaydebeapi
>>> conn = jaydebeapi.connect("net.sourceforge.jtds.jdbc.Driver",
...                           "jdbc:jtds:sybase://t016100.lewis.co.za:5000;DatabaseName=REDLEWIS",
...                           ["lewis", "redpassword"],
...                           "/path/to/jtds.jar",)
>>> curs = conn.cursor()
>>> curs.execute('create table CUSTOMER'
...                '("CUST_ID" INTEGER not null,'
...                ' "NAME" VARCHAR not null,'
...                ' primary key ("CUST_ID"))'
...             )
>>> curs.execute("insert into CUSTOMER values (1, 'John')")

>>> curs.close()
>>> conn.close() 


def query_with_fetchall():
    try:
        dbconfig = read_db_config()
        conn = MySQLConnection(**dbconfig)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()
 
        print('Total Row(s):', cursor.rowcount)
        for row in rows:
            print(row)
 
    except Error as e:
        print(e)
 
    finally:
        cursor.close()
        conn.close()
 
 
if __name__ == '__main__':
    query_with_fetchall()