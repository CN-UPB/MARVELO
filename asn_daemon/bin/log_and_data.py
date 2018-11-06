import os

#---------------------------------------------------------
#function: create_log
#arguments:
#  - path: string with path of the logfile
#---------------------------------------------------------
def create_log(path):
    global logfile
    logfile = open(path,'a',0)


#---------------------------------------------------------
#function: log
#arguments:
#  - message: string with message to write to logfile
#---------------------------------------------------------
def log(message):
    print('Message-->',message)
    logfile.write(str(message))
    logfile.write('\n')


#---------------------------------------------------------
#function: delete_data
#---------------------------------------------------------
def delete_data():
    log("Delete data in system folder")
    os.system("rm -f -r system/*")
