#!/opt/wiarne/bin/python
import xml.etree.ElementTree as ET
import sys
sys.path.append('/opt/wiarne/monitoring_scripts')
try:
    import wiarne_api
    import wiarne_api.ssh_api
    from paramiko.ssh_exception import BadHostKeyException, AuthenticationException, SSHException, NoValidConnectionsError
except ImportError:
    print("failed to import wiarne_api")
    
try:
    pass
    #client = wiarne_api.init_connection(user='monitor', password='adtQVURnPX4EjcfT5V6sARr5S52DC2XQ')
except Exception as err:
    print("error creating client")
    client = None
    print(err)
    
# tree = ET.parse('allocation.xml')
tree = ET.parse('/home/asn/asn_server/Demos/topology/IntensiveSourceSeparation/ica_3dist.xml')
#tree = ET.parse('/home/asn/asn_server/bin/simParam/allocation.xml')
root = tree.getroot()
#print(root)
args = []

for node in root.findall('node'):
    args.clear()
    for algorithm in node.findall('algorithm'):
        for parameter in algorithm.findall('parameter'):
            temp_string = (algorithm.get('executable')).split('/')[1] #+' '+str(parameter.get('param')))
            args.append(temp_string)
    print(args)
    try:
        wiarne_api.ssh_api.set_attributes(node.get('pi_id'), args)
        for arg in args:
           o,e= wiarne_api.ssh_api._config_script(node.get('pi_id'), "ProcessMonitor", "processes", [arg], mode="add", userpi='asn',
                                   pwdpi='asn')
           print (e)
    except NoValidConnectionsError as exc:
        print(str(exc))
