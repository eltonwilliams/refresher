import jaydebeapi
conn = jaydebeapi.connect("net.sourceforge.jtds.jdbc.Driver",
                              "jdbc:jtds:sybase://t106700.lewis.co.za:5000;DatabaseName=REDLEWIS",
                              ["lewis", "redpassword"],
                              "/app/Refresher/jtds.jar",)
curs = conn.cursor()
curs.execute("select * from branch_control")
db = curs.fetchall()
for i in db[0]:
    print (i)
curs.close()
conn.close() 
