import multiprocessing as mp
import random ,sys,time
import string

random.seed(123)


def r_intensive_func (itime):
    start = time.time()
    while time.time()-start <itime:
        v = (time.time()-start)/itime*100
        sys.stdout.write("\r%d%%" % v )
        sys.stdout.flush()
        100**100
    print "Done"
# define a example function
def rand_string(length, pos, output):
    """ Generates a random string of numbers, lower- and uppercase chars. """
    rand_str = ''.join(random.choice(
                        string.ascii_lowercase
                        + string.ascii_uppercase
                        + string.digits)
                   for i in range(length))
    output.put((pos,rand_str))

def r_intensive(x, pos, output):
    while True:#for i in range(100):
        5*5
    output.put((pos,"finished"))
if __name__ == "__main__" :
    # Define an output queue
    output = mp.Queue()
    # Setup a list of processes that we want to run
    # processes = [mp.Process(target=rand_string, args=(5, output)) for x in range(4)]
    processes = []
    # for x in range(4):
    #     processes.append(mp.Process(target=rand_string, args=(5, x, output)))
    # processes.append(mp.Process(target=r_intensive, args=(5,100, output)))
    processes.append(mp.Process(target=r_intensive_func, args=[3]))
    processes.append(mp.Process(target=r_intensive_func, args=[3]))

   # Run processes
    for p in processes:
        p.start()

    # Exit the completed processes
    for p in processes:
        p.join()

    # Get process results from the output queue
    # results = [output.get() for p in processes]

    print "done"
    # results.sort()
    # print(results)