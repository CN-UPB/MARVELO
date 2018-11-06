import sys,os
command = "nc -d -l " + sys.argv[1] + " > " + sys.argv[2]
while(1):
    os.system(command)
