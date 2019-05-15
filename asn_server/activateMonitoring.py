#!/opt/wiarne/bin/python
import wiarne_api as api
from wiarne_api import ssh_api
CLIENT = api.init_connection(user='wine',password='6gFq7rUDTSbhPTxnj79LNrDxK388yXVG', host="10.0.1.11")
							 
#pi_ip  = "192.168.10.207"


#api.arcs_diarization(CLIENT, path="None")
#api.appSim_diarization(CLIENT, path="None")

pi_ips  = ["10.0.1.12","10.0.1.13","10.0.1.14"]
for pi_ip in pi_ips:
	script = "RateMonitor"
	out,err = ssh_api.activate_script(pi_ip, script,userpi = 'asn', pwdpi='asn')
	script = "CommonMonitor"
	out,err = ssh_api.activate_script(pi_ip, script,userpi = 'asn', pwdpi='asn')
	script = "NetworkMonitor"
	out,err = ssh_api.activate_script(pi_ip, script,userpi = 'asn', pwdpi='asn')
	script = "ProcessMonitor"
	out,err = ssh_api.activate_script(pi_ip, script,userpi = 'asn', pwdpi='asn')
	script = "IwconfigMonitor"
	out,err = ssh_api.activate_script(pi_ip, script,userpi = 'asn', pwdpi='asn')
	out,err = ssh_api.set_hostServer(pi_ip,userpi = 'asn', pwdpi='asn')

	#api.appSim_diarization(CLIENT, path="None")
	#api.arcs_diarization(CLIENT, path="None")
	#api.appSim_diarization(CLIENT, path="None")
	#api.nodeSim_diarization(CLIENT, path="None")



#api.dropMeasurements(user='admin', password = 'sRGYdrT9cW5NeptCGt7NSr8476uAAeCs',   host="10.0.1.11", measurements =["ProcessMonitor"])