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
#----------------------------------------------------------------
def configure(client, param):
  total = ""
  for key, value in param.iteritems():
    if type(value) == type({}):
      total += "\n[" + key + "]\n"
      for key2, value2 in value.iteritems():
		if value2 != "":
			total += key2 + " = " + unicode(value2) + "\n"
    
  stdin, stdout, stderr = client.exec_command("echo '%s' >> /opt/stack/tempest/etc/mytempest.conf" %total)

#-------------MAIN--------------------------------------------
host = "192.168.0.250"
user = "stack"
psw = "stack"

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
configuration = { "auth" : { "use_dynamic_credentials" : True, "tempest_roles" : "Member", "admin_domain_name" : "Default", "admin_tenant_name" : "admin", "admin_password" : "password", "admin_username" : "admin" }, "baremetal" : "", "boto" : "", "cli" : { "cli_dir" : "/usr/local/bin" }, "compute" : { "fixed_network_name" : "private", "ssh_connect_method" : "floating", "flavor_ref_alt" : 84, "flavor_ref" : 42, "image_alt_ssh_user" : "cirros", "image_ref_alt" : "a60350e5-3f33-405c-8118-94acc0fe1738", "image_ref" : "a60350e5-3f33-405c-8118-94acc0fe1738", "ssh_user" : "cirros", "build_timeout" : 196 }, "compute-admin" : "", "compute-feature-enabled" : { "allow_duplicate_networks" : True, "attach_encrypted_volume" : True, "live_migrate_paused_instances" : True, "preserve_ports" : True, "api_extensions" : "all", "block_migration_for_live_migration" : False, "change_password" : False, "live_migration" : False, "resize" : True, "max_microversion" : "latest" }, "dashboard" : { "dashboard_url" : "http://192.168.0.180/" }, "data_processing" : "", "database" : "", "dns" : "", "dns-admin" : "", "identity" : { "auth_version" : "v2", "uri_v3" : "http://192.168.0.180:5000/v3", "uri" : "http://192.168.0.180:5000/v2.0/" }, "identity-feature-enabled" : "", "image" : "", "image-feature-enabled" : { "deactivate_image" : True }, "input-scenario" : "", "negative" : "", "network" : { "default_network" : "10.0.0.0/24", "public_router_id" : "", "public_network_id" : "", "tenant_networks_reachable" : False, "api_version" : "2.0" }, "network-feature-enabled" : { "api_extensions" : "all", "ipv6_subnet_attributes" : True, "ipv6" : True }, "object-storage" : "", "object-storage-feature-enabled" : { "discoverable_apis" : "all" }, "orchestration" : "", "oslo_concurrency" : { "lock_path" : "/opt/stack/data/tempest" }, "queuing" : "", "scenario" : { "large_ops_number" : 0, "img_file" : "cirros-0.3.4-x86_64-disk.img", "aki_img_file" : "cirros-0.3.4-x86_64-vmlinuz", "ari_img_file" : "cirros-0.3.4-x86_64-initrd", "ami_img_file" : "cirros-0.3.4-x86_64-blank.img", "img_dir" : "/home/stack/devstack/files/images/cirros-0.3.4-x86_64-uec" }, "service_available" : { "trove" : False, "ironic" : False, "sahara" : False, "horizon" : True, "ceilometer" : False, "heat" : False, "swift" : True, "cinder" : True, "neutron" : True, "nova" : True, "glance" : True, "key" : True }, "stress" : "", "telemetry" : "", "telemetry-feature-enabled" : { "events" : True }, "validation" : { "network_for_ssh" : "private", "image_ssh_user" : "cirros", "ssh_timeout" : 196, "ip_version_for_ssh" : 4, "run_validation" : False, "connect_method" : "floating" }, "volume" : { "build_timeout" : 196 }, "volume-feature-enabled" : { "backup" : False, "api_extensions" : "all", "incremental_backup_force" : True, "extend_with_snapshot" : True, "bootable" : True } }
#---------------------
#Verificare che numero di test sia uguale a numero di obiettivi
ris = []
configure(client,configuration)

for elem in testinstances.values():
        ris.append(test_scenario(client, elem))

print "------------------------RISULTATI-------------------------"
stampa = calc_time(ris,"det")
for elem in stampa:
  print elem

print compare_result(stampa, dacontrollare)
print "------------------------RISULTATI-------------------------"
