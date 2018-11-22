from django.shortcuts import render
from celery import Celery
import time, paramiko, re
from testboxes.models import UAT,QA
import socket
import urllib.request

app = Celery('tasks', backend='rpc://', broker='amqp://reduser:redpassword@rabbit//')

    
def connect(server=None):  ###remember to close client after user!!!
    
    ###TODO: temp for testing
    if server == "n010800.lewis.co.za":
        server = "10.150.60.1"

    if server == "t013200.lewis.co.za":
        server = "t013200.test.redpandasoftware.co.za"

    
    ### initialize NULL values
    useKey = None
    passw = None

    ### determine if LEWDEV is to be used
    if server:
        useKey = '/app/Refresher/keys/id_dsa'
    else:
        server = '10.100.1.97'
        passw = 'caveman'
    
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())

    print("Connecting to {}\n".format(server))
    client.connect(server, username='root', password=passw, key_filename=useKey)
    print("Connected to {}\n".format(server))

    return client

def obj_handler(result):
    result_list = []
    for line in result:
        if line.startswith('/u1/le/release/'):
            result = re.search('/u1/le/release/(.*)/red', line)
            result_list.append(result.group(1))
            
    return max(result_list)

def copy_obj(new_obj,server):
    sshServer=server
    lewdev = connect()


    obj_list = []
    for obj in new_obj:
        stdin, stdout, stderr = lewdev.exec_command('locate red{}.sql.Z'.format(obj))
        lists = stdout.readlines()
        lists = list(filter(None, lists))
        obj_list.append(obj_handler(lists))

    copy_list = []
    for obj in obj_list:
        copy_list.append('scp /u1/le/release/{}/Obj.{} {}:/le0/release/'.format(obj,obj,sshServer[:7]))


    for copy in copy_list:
        print("LEWDEV: running - {}".format(copy))
    
    for copy in copy_list:
        stdin, stdout, stderr = lewdev.exec_command(copy)

    lewdev.close()

def fetch(server,query):
    try:
        conn = jaydebeapi.connect("net.sourceforge.jtds.jdbc.Driver",
                              "jdbc:jtds:sybase://{}:5000;DatabaseName=REDLEWIS".format(server),
                              ["lewis", "redpassword"],
                              "/app/Refresher/jtds.jar",)
           
        curs = conn.cursor()
        curs.execute(query)
        rows = curs.fetchall()
        for row in rows:
            print(row)
        
        curs.close()
        conn.close()
        return rows
 
    except Exception as Error:
        print(type(Error))
        print(Error)
        return Error

def update(server,query):
    try:
        conn = jaydebeapi.connect("net.sourceforge.jtds.jdbc.Driver",
                              "jdbc:jtds:sybase://{}:5000;DatabaseName=REDLEWIS".format(server),
                              ["lewis", "redpassword"],
                              "/app/Refresher/jtds.jar",)
           
        curs = conn.cursor()
        curs.execute(query)
        #conn.commit()
        curs.close()
        conn.close()
        return "update success"

        
 
    except Exception as Error:
        print(type(Error))
        print(Error)
        return Error
    

@app.task
def sybase():
    query_string = """UPDATE employee SET password = 'uZ5/tJEv03Bq2';
UPDATE branch_process_control SET run_time_schedule = 'Minute1' , is_active = 1
    WHERE process_name IN 
        ('Send New Switched Branch Txns to Central',
        'Fetch New Switched Branch Txns From Central',
        'Send Modified Switched Branch Txns to Central',
        'Process Switched Branch Txn at Branch',
        'Fetch Modified Switched Branch Txns From Central',
        'SubAccountAndClubDocumentSync',
        'QrCodeCleanup');

UPDATE branch_process_control SET run_time_schedule = 'Minute15' , is_active = 1
    WHERE process_name IN ('Monitor Branch Processes');

UPDATE branch_process_control SET run_time_schedule = 'Custom' , is_active = 0
    WHERE process_name IN ('Branch StartOfDay Action Processor')

UPDATE branch_control SET system_locked = 0, system_status = '';

UPDATE branch_process_action SET continute_auth_code = 0, run_status = 'Unknown', run_comments = 'All stages run successfully'

UPDATE branch_control SET qr_code_enabled = 1;"""

query_string2 = """UPDATE employee SET password = 'Mine';
UPDATE branch_process_control SET run_time_schedule = 'Minute4' , is_active = 0
    WHERE process_name IN 
        ('Send New Switched Branch Txns to Central',
        'Fetch New Switched Branch Txns From Central',
        'Send Modified Switched Branch Txns to Central',
        'Process Switched Branch Txn at Branch',
        'Fetch Modified Switched Branch Txns From Central',
        'SubAccountAndClubDocumentSync',
        'QrCodeCleanup');

UPDATE branch_process_control SET run_time_schedule = 'Minute14' , is_active = 0
    WHERE process_name IN ('Monitor Branch Processes');

UPDATE branch_process_control SET run_time_schedule = 'TCustom' , is_active = 1
    WHERE process_name IN ('Branch StartOfDay Action Processor')

UPDATE branch_control SET system_locked = 1, system_status = 'test';

UPDATE branch_process_action SET continute_auth_code = 1, run_status = 'Isknown', run_comments = 'All stages run testfully'

UPDATE branch_control SET qr_code_enabled = 0;"""

@app.task 
def process(group, branch, server, DB, desktop, restore, user):
    
   
    prefix = branch[:1]
    branch = branch[1:]

    if group == 'UAT':
        update_message = UAT.objects.filter(prefix= prefix, server = branch)
        update_progress = UAT.objects.filter(prefix= prefix, server = branch)
        update_taskid = UAT.objects.filter(prefix= prefix, server = branch)
    else:
        update_message = QA.objects.filter(prefix= prefix, server = branch)
        update_progress = QA.objects.filter(prefix= prefix, server = branch)
        update_taskid = QA.objects.filter(prefix= prefix, server = branch)

    if server == "t013200.lewis.co.za":
        server = "t013200.test.redpandasoftware.co.za"

    print(server)
    if server != "n010800.lewis.co.za":
        if server == "t018800.lewis.co.za":
            update_message.update(message = "Step 1/5 :	Skipping Brance/Tranlog Services (no workstation)")

        else:
            # stop brach and tranlog service
            wksip = '{}.51'.format(socket.gethostbyname(server).rsplit('.', 1)[0])
            update_message.update(message = "Step 1/5 :	Stopping/Disabling Brance Service")
            feedback = (urllib.request.urlopen("http://{}/ws/util.asp?servstop=branchservice".format(wksip)).read()).decode("utf-8")
            print("branch service stop = {}".format(feedback))
            update_message.update(message = "Step 1/5 :	Stopping/Disabling Tranlog Service")
            feedback = (urllib.request.urlopen("http://{}/ws/util.asp?servstop=tranlogservice".format(wksip)).read()).decode("utf-8")
            print("tranlog service stop = {}".format(feedback))

        lewdev = connect()
        update_message.update(message = "Step 1/5 :	Sending files needed for refresh...")
        stdin, stdout, stderr = lewdev.exec_command('scp /u/ejw/toBox/x.refresh* {}00:/tmp/'.format(prefix.lower()+branch.zfill(4)))
        stdout.channel.recv_exit_status()
        lewdev.close()
    
    


    #connecting to server
    client = connect(server)

    update_message.update(message = "Step 1/5 :	Starting refresh process for {}.".format(prefix+branch))


    ##actual procedure
    if restore:
        update_message.update(message = "Step 2/5 :	Extracting CERES files...")
        print('EXTRACTING: tar -xf /le0/backupsybase/data/{}.ceres.tar -C /le0/{}/00/'.format(branch.zfill(4),branch.zfill(4)))
        stdin, stdout, stderr = client.exec_command('tar -xf /le0/backupsybase/data/{}.ceres.tar -C /le0/{}/00/'.format(branch.zfill(4),branch.zfill(4)))
        stdout.channel.recv_exit_status()
        stdin, stdout, stderr = client.exec_command('gunzip -f /le0/{}/00/*.gz'.format(branch.zfill(4)))
        stdout.channel.recv_exit_status()
        
        
    
    stdin, stdout, stderr = client.exec_command('echo $HOSTNAME')
    hostname = stdout.readline()

    print("restarting sybase on {}".format(hostname))
    update_message.update(message = "Step 2/5 :	Restarting the sybase service.")
    stdin, stdout, stderr = client.exec_command('service sybase restart')
    time.sleep(20)


    print("loadDB")
    update_message.update(message = "Step 2/5 :	Starting load of 'REDLEWIS' database.")
    stdin, stdout, stderr = client.exec_command('/tmp/x.refresh.isqlload')

    retryTriggers = ["Unable to obtain exclusive access to database 'REDLEWIS'.",
    "ct_connect(): user api layer: internal Client Library error: Read from the server has timed out.",
    "Database 'REDLEWIS' has not been recovered yet - please wait and try again."]
    
    while True:
        stdin, stdout, stderr = client.exec_command('tail -1 /tmp/testdmp.log')
        outp = stdout.readline()
        print(outp)
        if any(x in outp for x in retryTriggers):
            print("inside conditional if loop")
            update_message.update(message = "Step 2/5 :	Unable to obtain exclusive access to database 'REDLEWIS'.")
            stdin, stdout, stderr = client.exec_command('service sybase stop')
            time.sleep(20)
            update_message.update(message = "Step 2/5 :	Attempting another load.")
            stdin, stdout, stderr = client.exec_command('service sybase start')
            time.sleep(40)
            stdin, stdout, stderr = client.exec_command('/tmp/x.refresh.isqlload')
            stdin, stdout, stderr = client.exec_command('tail -1 /tmp/testdmp.log')
            outp = stdout.readline()
            print("Trying again.")

        elif re.search(r'\((.*?)\)',outp):
            try:
                newp = re.search(r'\((.*?)\)',outp).group(1)
                interger = int(newp.strip('%')) 
                break 
            except Exception as e:
                continue

    update_message.update(message = "Step 2/5 :	Loading database 'REDLEWIS' in progress.")
    newp = "0%"
    while int(newp.strip('%')) < 99:
        stdin, stdout, stderr = client.exec_command('tail -1 /tmp/testdmp.log')
        outp = stdout.readline()
        if re.search(r'\((.*?)\)',outp):
            if re.search(r'\((.*?)\)',outp).group(1) != newp:
                newp = re.search(r'\((.*?)\)',outp).group(1)
                try:
                    interger = int(newp.strip('%'))  
                except Exception as e:
                    break
                update_progress.update(progress = int(newp.strip('%')))
                print(newp)
        else:
            break
       
    
    update_progress.update(progress = 100)
    update_message.update(message = "Step 2/5 :	Waiting for database 'REDLEWIS' to go online.")

    newp = "no output"
    while True:
        stdin, stdout, stderr = client.exec_command('tail -1 /tmp/testdmp.log')
        outp = stdout.readline()
        if newp != outp:
            newp = outp
            print(newp.strip())
            if "Database 'REDLEWIS' is now online." in newp:
                break
    
    print("adding refresh lock -> echo '1' > /le0/pbin/LCK..drun")
    update_message.update(message = "Step 3/5 :	adding refresh lock...")
    stdin, stdout, stderr = client.exec_command("echo '1' > /le0/pbin/LCK..drun")

    
    update_progress.update(progress = 0)
    update_message.update(message = "Step 3/5 :	Database 'REDLEWIS' is now online.")

    stdin, stdout, stderr = client.exec_command('x.getver.pl')
    lists = stdout.readlines()
    dbver = (lists[0].strip())
    dbversion = (lists[0].strip())[3:]
    print("DBVERSION  >>>>>> AFTER LOAD >>>>>>  ",dbversion)



    dblist = []
    dbout = []
    stdin, stdout, stderr = client.exec_command('ls /le0/redlewis/scheme/red*.sql')
    lists = stdout.readlines()
    
    if len(lists) > 0:
        new = []
        for i in lists:
            result = re.search('/le0/redlewis/scheme/red(.*).sql\n', i)
            new.append(result.group(1))

     

        inp = int(dbversion)

        rem = []
        for i in new:
            try:
                int(i)
            except Exception as e:
                continue
            if int(i) > inp:
                rem.append(i)

    if rem:
        for i in rem:
            print('Removing red{}.sql...'.format(i))
            stdin, stdout, stderr = client.exec_command('rm -rf /le0/redlewis/scheme/red{}.sql'.format(i)) 
    print('Restarting sybase...')
    update_message.update(message = "Step 3/5 :	Restarting the sybase service.")
    stdin, stdout, stderr = client.exec_command('service sybase restart')
    time.sleep(20)


    new_obj = []

    obj = int(inp)+1
    while obj <= int(DB):
        new_obj.append('0'+str(obj))
        obj+=1

    sshServer = '{}{}00'.format(prefix.lower(),branch.zfill(4))
    print("Updates to be copied from lewdev to {} is:".format(sshServer))
    for obj in new_obj:
        print(obj)

    copy_obj(new_obj,sshServer)    

    print('RUNNING x.redlewis.wip.update.pl')
    stdin, stdout, stderr = client.exec_command('/le0/redlewis/x.redlewis.wip.update.pl')
    stdout.channel.recv_exit_status()

    print('copying xtable data')
    update_message.update(message = "Step 3/5 :	Copying xtable data")
    lewdev = connect()
    stdin, stdout, stderr = lewdev.exec_command('scp /u/omega/dbnxtabl* {}00:/le0/{}/00/'.format(prefix.lower()+branch.zfill(4), branch.zfill(4)))
    stdout.channel.recv_exit_status()
    lewdev.close()

    print('RUNNING redSOD.sh')
    update_message.update(message = "Step 3/5 :	Running redSOD.sh...")
    stdin, stdout, stderr = client.exec_command('/le0/pbin/redSOD.sh')
    stdout.channel.recv_exit_status()
    update_message.update(message = "Step 3/5 :	Inserting test enviroment settings into the 'REDLEWIS' database.")
   
    SQL = """update employee set password = 'uZ5/tJEv03Bq2';

update branch_process_control set run_time_schedule = 'Minute1', is_active = 1 where process_name in ('Send New Switched Branch Txns to Central', 
                                                                                                      'Fetch New Switched Branch Txns From Central', 
                                                                                                      'Send Modified Switched Branch Txns to Central', 
                                                                                                      'Process Switched Branch Txn at Branch', 
                                                                                                      'Fetch Modified Switched Branch Txns From Central');

update branch_process_control set run_time_schedule = 'Minute15' , is_active = 1 where process_name in ('Monitor Branch Processes');

update branch_process_control set  run_time_schedule = 'Custom' , is_active = 0 where process_name in ('Branch StartOfDay Action Processor');

update branch_control set system_locked = 0, system_status = '';

update branch_process_action set continute_auth_code = 0, run_status = 'Unknown', run_comments = 'All stages run successfully';

update branch_control set qr_code_enabled = 1;"""

    print('running SQL: RESET SOD AND ACTIVATE SWITCHING PROCESSES')
    update_message.update(message = "Step 3/5 :	Running SQL: reset SOD and activating switching processes...")
    stdin, stdout, stderr = client.exec_command('/le0/redlewis/sql.sh /tmp/x.refresh.testbox.sql')
    stdout.channel.recv_exit_status()
    print(SQL)

    print('removing refresh lock -> rm -f /le0/pbin/LCK..drun')
    update_message.update(message = "Step 3/5 :	Removing refresh lock...")
    stdin, stdout, stderr = client.exec_command('rm -f /le0/pbin/LCK..drun')

    print('RUNNING x.brn.demon')
    update_message.update(message = "Step 4/5 :	Running x.brn.demon...")
    stdin, stdout, stderr = client.exec_command('/le0/pbin/x.brn.demon')
    while True:
        stdin, stdout, stderr = client.exec_command('x.getver.pl')
        lists = stdout.readlines()
        try:
            dbver = (lists[0].strip())
            dbversion = (lists[0].strip())[3:]
            time.sleep(20)
            print("LOOP DBVERSION >>> "+dbversion[1:]+"<<   >> entered DB >>"+DB)
            if int(dbversion) == int(DB):
                break
            else:
                update_message.update(message = "Step 4/5 :	Running x.brn.demon - applying DB0{}".format(int(dbversion)+1))

        except Exception as e:
            print(e)

    
    update_message.update(message = "Step 4/5 :	Unlocking system.")
    stdin, stdout, stderr = client.exec_command('/le0/pbin/unlocksys')
    stdin.write('Y\n')
    stdin.flush()
    stdout.channel.recv_exit_status()


    
    client.close()

    if server != "n010800.lewis.co.za":
        lewdev = connect()
        update_message.update(message = "Step 4/5 :	Removing refresh files from /tmp...")
        stdin, stdout, stderr = lewdev.exec_command('rm /tmp/x.refresh.{x.refresh.testbox.sql,x.refresh.isqlload,x.refresh.sqlreload}')
        stdout.channel.recv_exit_status()

        if server == "t018800.lewis.co.za":
            update_message.update(message = "Step 5/5 :	Skipping enabling Brance/Tranlog Services (no workstation)")

        else:
            # start brach and tranlog service
            wksip = '{}.51'.format(socket.gethostbyname(server).rsplit('.', 1)[0])
            update_message.update(message = "Step 5/5 :	Starting/Enabling Brance Service")
            feedback = (urllib.request.urlopen("http://{}/ws/util.asp?servstart=branchservice".format(wksip)).read()).decode("utf-8")
            print("branch service start = {}".format(feedback))
            update_message.update(message = "Step 5/5 :	Starting/Enabling Tranlog Service")
            feedback = (urllib.request.urlopen("http://{}/ws/util.asp?servstart=tranlogservice".format(wksip)).read()).decode("utf-8")
            print("tranlog service start = {}".format(feedback))


    update_message.update(message = "Step 5/5 :	Refresh completed successfully")
    update_taskid.update(taskid = 'None')
    
    return 'success'
