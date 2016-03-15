__author__ = "Matteo De Marie"
__email__ = "de.marie.matteo@gmail.com"

from testagent.probe import Probe
import paramiko
from datetime import datetime
import time

class perftemp(Probe):
#------------Exec tests and parse logs----------------------------
  def core(self,inputs):
    def test_scenario(client, scen_name):
            #Check number of next test
            cmin, cmout, cmerr = client.exec_command("cat /opt/stack/tempest/.testrepository/next-stream")
            num = cmout.read()
	    #Start test
            cmin, cmout, cmerr = client.exec_command("/opt/stack/tempest/run_tempest.sh -t tempest." + scen_name)
            #Wait for result
            
            while not cmout.channel.exit_status_ready():
              pass
            
            #Check results based on test number        
            cmin, cmout, cmerr = client.exec_command("cat /opt/stack/tempest/.testrepository/"+num)
            
            results = []	#list of test with detail
            elem = {}		#detail of test
            start = False	#timestamp test started found
            test = False	#name test found
            result = False	#result's test found
            
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
    #----Type of times regroup-------------------------------------
    #Type 'sum': Sum times all tests
    #Type 'par': Sum times all subtests
    #Type 'det': Show times all subtests
    
    def calc_time(data, tipo="par"):
      total = []
      if tipo == "sum":
        temp = None
        for test in data:
          for sub in test:
            if sub.get("result") == "skipped":
              skip_all = []
              skip_all.append("skipped")
              return skip_all
            elif sub.get("result") == "failed":
              all_failed = []
              all_failed.append("failed")
              return all_failed
            else:
              if temp is None:
                temp = (sub.get("end")-sub.get("start"))
              else:
                temp = temp + (sub.get("end")-sub.get("start"))
       
        total.append(temp)
        
      elif tipo == "par":
        temp = None
        for test in data:
          for sub in test:
            if sub.get("result") == "skipped":
              temp = "skipped"
              break
            elif sub.get("result") == "failed":
              temp = "failed"
              break
            else:
              if temp is None:
                temp = (sub.get("end")-sub.get("start"))
              else:
                temp = temp + (sub.get("end")-sub.get("start"))
          total.append(temp)
          temp = None
        
      elif tipo == "det":
        for test in data:
          for sub in test:
            if sub.get("result") == "skipped":
              total.append("skipped")
              break
            elif sub.get("result") == "failed":
              total.append("failed")
              break
            else:
              total.append(sub.get("end")-sub.get("start"))
    
      else:
        return False
      
      return total  
    #-----Compare results with goal--------------------------------
    def compare_result(tested, goal):
      results = []

      for i in range(0,len(goal)):
        if tested[i] == "failed":
          #results.append("Failed")
		  results.append(False)
          continue
        elif tested[i] == "skipped":
          #results.append("False*")
		  results.append(False)
          continue
        elif tested[i].total_seconds() <= goal.get(str(i+1)):
          results.append(True)
        else:
          results.append(False)
      
      return results
    #-----Configure tempest.conf----------------------------------------
    def configure(client, param):
      total = ""
      for key, value in param.iteritems():
    	if key != "Tempest" or key != "Aspected" or key != "Tests":
    		if type(value) == type({}):
    		  total += "\n[" + key + "]\n"
    		  for key2, value2 in value.iteritems():
    			if value2 != "":
    				total += key2 + " = " + unicode(value2) + "\n"
        
      stdin, stdout, stderr = client.exec_command("echo '%s' > /opt/stack/tempest/etc/tempest.conf" %total)
    #-------------MAIN--------------------------------------------
    xml = self.testinstances
    if len(xml["Tests"]) != len(xml["Aspected"]):
    	return "Quantita di valori attesi diversa dal numero di test"

    try:
      client = paramiko.SSHClient()
      client.load_system_host_keys()
      client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      client.connect(xml["Tempest"]["host"], username=xml["Tempest"]["user"], password=xml["Tempest"]["psw"])
    except:
      print "Impossibile connettersi al server Tempest"
      if client:
        client.close()
      return "Impossibile connettersi al server Tempest"
    
    results = []
    
    print "Start configuration"
    configure(client,xml)
    print "Finish configuration"
    
    print "Start testing"

    for i in range(1,len(xml["Tests"])+1):
        results.append(test_scenario(client,xml["Tests"][str(i)]))

    print "Finish testing"
    
    client.close()
    
    print "Regroup results"
    times = calc_time(results)
    print "Regroupped"
    
    print "Comparing results"
    return compare_result(times,xml["Aspected"])
    
  def corer (self, inputs):
        return

  def appendAtomics(self):
        self.appendAtomic(self.core, self.corer)
  
probe = perftemp
