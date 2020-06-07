import pickle

def loadVar(filename):
    return pickle.load(open(filename, "rb"))

def convertPickleToTxt(loc,nrNodes,nrApps,nrOfTrials,topology='linear',capacityList=[21]):

    for nr_nodes in nrNodes:
        for nr_apps in nrApps:
          for capacity in capacityList:
            print("Nr nodes: ", nr_nodes, "Nr blocks:" , nr_apps, "Capacity: ", capacity)

            for trialx in nrOfTrials:
               try:
                   loadPower = loadVar(loc + '/Power' + str(nr_nodes) + 'Topology' + str(topology) + 'Napps' + str(
                       nr_apps) + 'Cap' + str(capacity) + str(trialx) + '.pickle')
                   filename =  'resultsTxt/'+'n'+str(nr_nodes)+'b'+str(nr_apps)+'s'+str(trialx)
                   file = open(filename+".txt", "w+")
                   # Number of time slots
                   file.write(str(loadPower['number']))
                   # embedding on tasks o nodes: (task,X,node)
                   file.write(str(loadPower['map']))
                   # routes with schedueling: (task,X,tx_node,rx_node,timeslot)
                   file.write(str(loadPower['s']))
                   # print loadPower['number']
                   file.close()

               except Exception as e:
                       print(e)




convertPickleToTxt(loc='results',nrNodes=range(4,10),nrApps=range(3,7),nrOfTrials=range(50),topology='linear',capacityList=[21])