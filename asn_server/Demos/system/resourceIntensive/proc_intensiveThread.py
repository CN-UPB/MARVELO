#%---------------- Start Additional Resource intesive method
import threading, time, sys

runTime = 5
fileName = "pIntenseiv: "
def r_intensive_func (fileName,itime):
    start = time.time()
    while time.time()-start <itime:
        v = int ((time.time()-start)/itime*100)
        sys.stdout.write("\r%s%%" % fileName+ str(v) )
        sys.stdout.flush()
        100**100
    print "\nDone"
thread = threading.Thread(target=r_intensive_func, args=[fileName,runTime])
print "Start\n"
thread.start()
#%---------------- End Additional Resource intesive method
