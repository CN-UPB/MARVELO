#!/opt/wiarne/bin/python

import wiarne_api as api
from wiarne_api import ssh_api
CLIENT = api.init_connection(user='wine',
                             password='6gFq7rUDTSbhPTxnj79LNrDxK388yXVG', host="10.0.1.11")

#api.dropMeasurements(user='admin', password = 'sRGYdrT9cW5NeptCGt7NSr8476uAAeCs',   host="10.0.1.11", measurements =["ProcessMonitor"])

#api.dropMeasurements(user='admin', password = 'sRGYdrT9cW5NeptCGt7NSr8476uAAeCs',   host="10.0.1.11")

api.dropMeasurements(user='admin', password = 'sRGYdrT9cW5NeptCGt7NSr8476uAAeCs',   host="10.0.1.11", measurements =["RateMonitor"])
api.dropMeasurements(user='admin', password = 'sRGYdrT9cW5NeptCGt7NSr8476uAAeCs',   host="10.0.1.11", measurements =["ProcessMonitor"])
#api.dropMeasurements(user='admin', password = 'sRGYdrT9cW5NeptCGt7NSr8476uAAeCs',   host="10.0.1.11", measurements =["CommonMonitor"])
#api.dropMeasurements(user='admin', password = 'sRGYdrT9cW5NeptCGt7NSr8476uAAeCs',   host="10.0.1.11", measurements =["IwconfigMonitor"])
api.dropMeasurements(user='admin', password = 'sRGYdrT9cW5NeptCGt7NSr8476uAAeCs',   host="10.0.1.11", measurements =["NetworkMonitor"])


