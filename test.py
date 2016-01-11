
import paramiko
from datetime import datetime

def test_scenario(client, scen_name):
        #Check number of next test
        cmin, cmout, cmerr = client.exec_command("cat /opt/stack/tempest/.testrepository/next-stream")
        num = cmout.read()
        #Start test
        cmin, cmout, cmerr = client.exec_command("/opt/stack/tempest/run_tempest.sh tempest.scenario." + scen_name)
        #Wait for results
        while not cmout.channel.exit_status_ready():
          pass
        #Check results based on test number        
        cmin, cmout, cmerr = client.exec_command("cat /opt/stack/tempest/.testrepository/"+num)
        
        results = []
        elem = {}
        start = False
        test = False
        result = False

        for line in cmout.readlines():
          #Checked al details about one test
          if start and test and result: 
            results.append(elem)
            print "--------------------"
            elem = {}
            start = False
            test = False
            result = False
          #First 'time' time before start test
          elif line.startswith("time") and start==False:
            elem['start'] = datetime.strptime(line[6:-2],"%Y-%m-%d %H:%M:%S.%f")
            print "start: " + (datetime.strptime(line[6:-2],"%Y-%m-%d %H:%M:%S.%f")).ctime()
            start = True
          #Second 'time' time after test is done
          elif line.startswith("time") and start==True:
            elem['end'] = datetime.strptime(line[6:-2],"%Y-%m-%d %H:%M:%S.%f")
            print "end: " + (datetime.strptime(line[6:-2],"%Y-%m-%d %H:%M:%S.%f")).ctime()
          #Result of test SUCCESS
          elif line.startswith("successful:"):
            elem['result'] = "success"
            result = True
          #Result of test SKIPPED
          elif line.startswith("skip:"):
            elem['result'] = "skipped"
            result = True
          #Result of test FAILED
          elif line.startswith("failure:"):
            elem['result'] = "failed"
            result = True
          #Name of test
          elif line.startswith("test:"):
            elem['test'] = line[6:].split("[")[0]
            print "nome: " + line[6:].split("[")[0]
            test = True
                    
        return results    
#-----------------------------------------------------------------
#Tipo 'sum': Totale tempo di tutti i test
#Tipo 'par': Parziale per test principale
#Tipo 'det': Dettagliato per ogni sotto test 

def calc_time(data, tipo="sum"):
  tot = []
  if tipo == "sum":
    temp = None
    for test in data:
      for sub in test:
        if sub.get("result") == "skipped":
          pass
        elif sub.get("result") == "failed":
          all_failed = []
          all_failed.append("failed")
          return all_failed
        else:
          if temp is None:
            temp = (sub.get("end")-sub.get("start"))
          else:
            temp = temp + (sub.get("end")-sub.get("start"))
    tot.append(temp)
    
  elif tipo == "par":
    temp = None
    for test in data:
      for sub in test:
        if sub.get("result") == "skipped":
          pass
        elif sub.get("result") == "failed":
          temp = "failed"
          break
        else:
          if temp is None:
            temp = (sub.get("end")-sub.get("start"))
          else:
            temp = temp + (sub.get("end")-sub.get("start"))
      tot.append(temp)
      temp = None
    
  elif tipo == "det":
    for test in data:
      for sub in test:
        if sub.get("result") == "skipped":
          pass
        elif sub.get("result") == "failed":
          tot.append("failed")
          break
        else:
          tot.append(sub.get("end")-sub.get("start"))

  else:
    return False
  
  return tot  
#-----------------------------------------------------------------
def compare_result(tested, goal):
  result = []
  print goal
 
  for i in range(0,len(goal)):
    #print tested[i].total_seconds() + " - %.6f" % goal.get(i+1)
    if tested[i] == "failed":
      result.append("Failed")
    elif tested[i].total_seconds() <= goal.get(i+1):
      result.append(True)
    else:
      result.append(False)
  
  return result
#-------------MAIN--------------------------------------------
#----------DA FILE XML-----------
host = "192.168.0.250"
user = "stack"
psw = "stack"
#-----------------------------
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
  client.connect(host, username=user, password=psw)
except:
  print "errore connessione"

stdin, stdout, stderr = client.exec_command("tempest --version")

for line in stdout.readlines():
        if "bash" in line:
                print "tempest non installato"
#-----DA FILE XML-----
dacontrollare = {1 : 3, 2 : 5}
testinstances = {1 : "test_dashboard_basic_ops", 2 : "test_server_basic_ops"}
#---------------------
#Verificare che numero di test sia uguale a numero di obiettivi
ris = []
for elem in testinstances.values():
        ris.append(test_scenario(client, elem))

print "------------------------RISULTATI-------------------------"
stampa = calc_time(ris,"det")
for elem in stampa:
  print elem

print compare_result(stampa, dacontrollare)
print "------------------------RISULTATI-------------------------"
