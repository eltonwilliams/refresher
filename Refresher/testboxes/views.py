from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from os import system, name
from testboxes.models import UAT,QA
from django.db import transaction
import paramiko
import threading
import re, time
import urllib.request
import socket
from celery.task.control import revoke
import jaydebeapi

from .tasks import *






### initial page for selecting the test boxes gets rendered here - reads from models.py
def index(request):
    try:
        UATList = UAT.objects.all().order_by('server')
        QAList = QA.objects.all().order_by('server')
        return render(request, 'dashboard.html', {'UAT': UATList,'QA': QAList})
        
    except Exception as e:
        print(e)
        return render(request, 'dashboard.html', {})



def selection(request):
    if 'server' in request.POST:
        prefix = request.POST['server'][:1]
        branch = request.POST['server'][1:]
        group = request.POST['group']
        if group == "UAT":
            has_taskid = UAT.objects.filter(prefix = prefix, server = branch).values('taskid').first()
        else:
            has_taskid = QA.objects.filter(prefix = prefix, server = branch).values('taskid').first()
        if has_taskid['taskid'] != 'None':
            return render(request, 'progress.html', {'group':group, 'branch':prefix+branch,'taskid':has_taskid['taskid']})
        else:
            status = getStatus(prefix, branch)
            server = "{}{}00".format(prefix.lower(),branch.zfill(4))
            return render(request, 'selection.html', {'group':group, 'branch': prefix+branch, 'status':status, 'server':server})

def apply(request):
    group = request.GET.get("group")
    prefix = request.GET.get("branch")[:1]
    branch = request.GET.get("branch")[1:]
    DB = request.GET.get("DB")
    user = request.GET.get("user")
    
    desktop = '35.1'
    #desktop = request.GET.get("Desktop")

    if request.GET.get("restore"):
        restore = True
    else:
        restore = False

    print(group+' - '+prefix+branch, DB, desktop, restore)
    if len(branch) > 1 and len(branch) < 5:
        server = '{}{}00.lewis.co.za'.format(prefix.lower(),branch.zfill(4))
    else:
        server = '{}{}00 is not a valid branch number'.format(prefix.lower(),branch.zfill(4))
    
    print(server)

    #print(user.first_name,user.last_name)
    
    result = process.delay(group, prefix+branch, server, DB, desktop, restore, user)
    print("passed task")
    if group == "UAT":
        update_taskid = UAT.objects.filter(prefix= prefix, server = branch).update(taskid = result.task_id)
        #update_user = UAT.objects.filter(prefix= prefix, server = branch).update(user = user)
    else:
        update_taskid = QA.objects.filter(prefix= prefix, server = branch).update(taskid = result.task_id)
        #update_user = QA.objects.filter(prefix= prefix, server = branch).update(user = user)
    
    return render(request, 'progress.html', {'group':group,'branch':prefix+branch,'taskid':result.task_id, 'user':user})

def task_control(request):
    print(request.POST)
    if 'cancel' in request.POST:
        task_id = request.POST['cancel']
        revoke(task_id, terminate=True)

    return render(request, 'completed.html', {})
    


def progress_update(request):
    group = request.POST['group']
    prefix = request.POST['branch'][:1]
    server = request.POST['branch'][1:]
    if group == "UAT":
        message = UAT.objects.filter(prefix = prefix, server = server).values('message').first()
        progress = UAT.objects.filter(prefix = prefix, server = server).values('progress').first()
        taskid = UAT.objects.filter(prefix = prefix, server = server).values('taskid').first()
    else:
        message = QA.objects.filter(prefix = prefix, server = server).values('message').first()
        progress = QA.objects.filter(prefix = prefix, server = server).values('progress').first()
        taskid = QA.objects.filter(prefix = prefix, server = server).values('taskid').first()
    print(taskid)
    data = {**message, **progress, **taskid}

    return JsonResponse(data)


def summary(request):
    prefix = request.GET.get("branch")[:1]
    branch = request.GET.get("branch")[1:]

    print(prefix+branch)

    status = getStatus(prefix, branch)
    print(status)
    return render(request, 'completed.html', {'branch': prefix+branch, 'status':status})



def getStatus(prefix, branch):
    status = {}


    if len(branch) > 1 and len(branch) < 5:
        server = '{}{}00.lewis.co.za'.format(prefix.lower(),branch.zfill(4))
    else:
        server = '{}{}00 is not a valid branch number'.format(prefix.lower(),branch.zfill(4))

    new = fetch(server,"select database_version from branch_control")
    #print(update(server,"update employee set password = 'uZ5/tJEv03Bq2'"))
    print("new>>",new)

    try:
        client = connect(server)
        stdin, stdout, stderr = client.exec_command('x.getver.pl')
        error = stderr.readlines()
        output = stdout.readlines()

        stdin, stdout, stderr = client.exec_command('date -r /data/backupsybase/data/{}.ceres.tar'.format(branch.zfill(4)))
        outc = stdout.readlines()
        if len(outc):
            filedate = '{} {} {}'.format(outc[0].split()[2],outc[0].split()[1],outc[0].split()[5])
            stdin, stdout, stderr = client.exec_command('ls -lh /data/backupsybase/data/{}.ceres.tar'.format(branch.zfill(4)))
            outc = stdout.readlines()
            size = outc[0].split()[4]
            tarinfo = "Size {} , Created {}".format(size,filedate)
        else:
            tarinfo = "/data/backupsybase/data/{}.ceres.tar - Not Found".format(branch.zfill(4))
     
        stdin, stdout, stderr = client.exec_command('date -r /data/backupsybase/data/REDLEWIS.dmp')
        outp = stdout.readlines()
        if len(outp):
            filedate = '{} {} {}'.format(outp[0].split()[2],outp[0].split()[1],outp[0].split()[5])
            stdin, stdout, stderr = client.exec_command('ls -lh /data/backupsybase/data/REDLEWIS.dmp')
            outp = stdout.readlines()
            size = outp[0].split()[4]
            dmpinfo = "Size {} , Created {}".format(size,filedate)
        else:
            dmpinfo = "/data/backupsybase/data/REDLEWIS.dmp - Not Found"

        if error:
            print(error[0])
            dbver = error[0].split('=')[-1]
        else:
            dbver = output[0].strip()

        client.close()

        if server == "t013200.lewis.co.za":
            server = "t013200.test.redpandasoftware.co.za"

        ###TODO: temp if statement for testing
        if server == "n010800.lewis.co.za" and dbver:
            status['Status'] = 'online'
            status['DB Version'] = dbver
            status['Desktop'] = "N/A"
            status['Branchservice'] = "N/A"
            status['REDLEWIS.dmp'] = dmpinfo 
            status['{}.ceres.tar'.format(branch.zfill(4))] = tarinfo 
        
        elif server == "t018800.lewis.co.za" and dbver:
            status['Status'] = 'online'
            status['DB Version'] = dbver
            status['Desktop'] = "N/A"
            status['Branchservice'] = "N/A"
            status['REDLEWIS.dmp'] = dmpinfo 
            status['{}.ceres.tar'.format(branch.zfill(4))] = tarinfo 

            
        else:
            wksip = '{}.51'.format(socket.gethostbyname(server).rsplit('.', 1)[0])
            desktop_release = (urllib.request.urlopen("http://{}/ws/util.asp?wsbuild=rl".format(wksip)).read()).decode("utf-8") 
            branchservice_release = (urllib.request.urlopen("http://{}/ws/util.asp?wsbuild=bs".format(wksip)).read()).decode("utf-8") 
            tranlog_release = (urllib.request.urlopen("http://{}/ws/util.asp?wsbuild=tl".format(wksip)).read()).decode("utf-8")
            print('DB Version : {}'.format(dbver))
            print('desktop_release : {}'.format(desktop_release))
            print('branchservice_release : {}'.format(branchservice_release))
            print('tranlog_release : {}\n\n'.format(tranlog_release))
            status['Status'], status['DB Version'],status['Desktop'], status['Branchservice'], status['Tranlog'], status['REDLEWIS.dmp'], status['{}.ceres.tar'.format(branch.zfill(4))]  = 'online',dbver,desktop_release,branchservice_release,tranlog_release, dmpinfo, tarinfo
    except Exception as e:
        print(e,"- While trying to connect to : "+server)
        status['Status'] = e
        status['DB Version'] = "N/A"
        status['Desktop'] = "N/A"
        status['Branchservice'] = "N/A"
        status['Tranlog'] = "N/A"
        status['REDLEWIS.dmp'] = "N/A" 
        status['{}.ceres.tar'.format(branch.zfill(4))] = "N/A"

    return status

def connect(server=None):  ###remember to close client after user!!!
    
    ###TODO: temp for testing
    if server == "n010800.lewis.co.za":
        server = "10.150.60.1"
    
    if server == "t013200.lewis.co.za":
        server = "t013200.test.redpandasoftware.co.za"

    print("inside connect > ", server)
    ### initialize NULL values
    useKey = None
    passw = None

    ### determine if LEWDEV is to be used
    if server:
        useKey = '/app/Refresher/keys/id_dsa'
        #useKey = 'C:\\Users\\eltonj\\Documents\\Docker\\project\\Refresher\keys\\id_dsa'
    else:
        server = '10.100.1.97'
        passw = 'caveman'
    
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())

    print("Connecting to {}\n".format(server))
    client.connect(server, username='root', password=passw, key_filename=useKey)
    print("Connected to {}\n".format(server))

    return client

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
 

            
 

import ldap
from django_auth_ldap import backend

def monkey(self, password):
  """
  Binds to the LDAP server with the user's DN and password. Raises
  AuthenticationFailed on failure.
  """
  if self.dn is None:
    raise self.AuthenticationFailed("failed to map the username to a DN.")

  try:
    sticky = self.settings.BIND_AS_AUTHENTICATING_USER

    self._bind_as(self.dn, password, sticky=sticky)

    # XXX: When binding as the user in Active Directory, the user details are
    # not made available until you search for them.
    if sticky and self.settings.USER_SEARCH:
      self._search_for_user_dn()

  except ldap.INVALID_CREDENTIALS:
    raise self.AuthenticationFailed("user DN/password rejected by LDAP server.")

backend._LDAPUser._authenticate_user_dn = monkey





