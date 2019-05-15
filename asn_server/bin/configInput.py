import pandas

trialx = 0

##
''' Directories with concrete values'''
'''

# # node
nodesfile = 'bin/simParam/nodeSim_' + str(trialx) + '.csv'
# component
appsfile = 'bin/simParam/sim_' + str(trialx) + '.csv'
# appSim
appSimFile = 'bin/simParam/appsim_11'+'.csv'
# edges
arcsfile = 'bin/simParam/arcs_' + str(trialx) + '.csv'
# vnf
chainsfile = 'bin/simParam/chain_' + str(1) + '.csv'

# nodesfile = 'simParam/nodeSim_' + str(trialx) + '.csv'
# # component
# appsfile = 'simParam/sim_' + str(trialx) + '.csv'
# # appSim
# appSimFile = 'simParam/appsim_11'+'.csv'
# # edges
# arcsfile = 'simParam/arcs_' + str(trialx) + '.csv'
# # vnf
# chainsfile = 'simParam/chain_' + str(1) + '.csv'

#load concrete parameters
# vnf data
chain_data = pandas.read_csv(chainsfile)
# node data
node_data = pandas.read_csv(nodesfile)
# component data
# appsfile_data = pandas.read_csv(appsfile).sort_values(by='quality', ascending=[False])
appsfile_data = pandas.read_csv(appSimFile)
# appPort data
appPort_data = pandas.read_csv(appSimFile)
# edges data
arc_data = pandas.read_csv(arcsfile)


#convert data into indexed set
# node set
node_data.set_index(['Node'], inplace=True)
node_data.sort_index(inplace=True)
# vnf set
chain_data.set_index(['srcapp', 'srcport','dstapp'], inplace=True)
chain_data.sort_index(inplace=True)
# appPort
appPort_data.set_index(['srcapp', 'port'], inplace=True)
appPort_data.sort_index(inplace=True)
# component set
# appsfile_data.set_index(['App'], inplace=True)
appsfile_data.set_index(['srcapp'], inplace=True)
# edge set
arc_data.set_index(['Start', 'End'], inplace=True)
arc_data.sort_index(inplace=True)

#extract indicies from data
# node index
node_set = node_data.index.unique()
node_set = [str(i) for i in node_set]
# edge index
arc_set = list(arc_data.index.unique())
arc_set = [(str(i[0]),str(i[1])) for i in arc_set]
# appPort index
appPort_set = appPort_data.index.unique()
# chain index
chain_set = chain_data.index.unique()
chain_set = sorted(chain_set, key=lambda tup: tup[1])
# chain_set = [(1,2),(2,3),(3,2),(3,4)]
# component inex
apps_set = set(appsfile_data.index.unique())
src = '127.0.0.1'
sinkNode = '127.0.0.1'
SINRth = 317
srcNode = '127.0.0.1'
sinkApp = './cov2svd.py'  # list(apps_set)[-1]
srcApp = './ica_readModule2.py'  # list(apps_set)[0]
srcApp2 = './ica_readModule.py'  # list(apps_set)[0]
srcAppList = [srcApp,srcApp2]
mapping_set = {(srcAppList[0], src), (srcAppList[1], src),
               (sinkApp, sinkNode)}  # {(list(apps_set)[0],src), (list(apps_set)[-1], sinkNode)}

maxTimeslots = 1
timeslots_set = range(1, maxTimeslots + 1)
timeBound = 3

bigM = 1e6

# timeslots_set = range(3, maxTimeslots + 1)
# SINRth = 2
# model.SINRth = 1.5
'''




'''Example dummy'''

nodesfile = 'bin/simParam/dummyExample/nodeSim_0'+ '.csv'
# component
appsfile = 'bin/simParam/dummyExample/sim_' + str(trialx) + '.csv'
# appSim
appSimFile = 'bin/simParam/dummyExample/appsim_1'+'.csv'
# edges
arcsfile = 'bin/simParam/dummyExample/arcs_0' + '.csv'
# vnf
chainsfile = 'bin/simParam/dummyExample/chain_' + str(1) + '.csv'



'''Example diariazation'''
nodesfile = 'bin/simParam/dummyExample/nodeSim_diarization'+ '.csv'
nodesfile = 'simParam/dummyExample/nodeSim_diarization'+ '.csv'
# component
appsfile = 'bin/simParam/dummyExample/sim_diarization' + '.csv'
# appsfile = 'simParam/dummyExample/sim_diarization' + '.csv'
# appSim
appSimFile = 'bin/simParam/dummyExample/appsim_diarization'+'.csv'
appSimFile = 'simParam/dummyExample/appsim_diarization'+'.csv'
# edges
arcsfile = 'bin/simParam/dummyExample/arcs_diarization' + '.csv'
arcsfile = 'simParam/dummyExample/arcs_diarization' + '.csv'
# vnf
chainsfile = 'bin/simParam/dummyExample/chain_diarization' + '.csv'
chainsfile = 'simParam/dummyExample/chain_diarization' + '.csv'

src ='10.0.1.2'
sinkNode='10.0.1.1'
srcApp = [1,3]#[list(apps_set)[0]]

givenPatha = 'Demos/system/spark3/'


'''Example Fobi'''

# nodesfile = 'bin/simParam/fobiExample/nodeSim_fobi.csv'
# nodesfile = 'simParam/fobiExample/nodeSim_fobi.csv'
# # component
# # appSim
# appSimFile = 'bin/simParam/fobiExample/appsim_fobi.csv'
# appSimFile = 'simParam/fobiExample/appsim_fobi.csv'
# # edges
# arcsfile = 'bin/simParam/fobiExample/arcs_fobi.csv'
# arcsfile = 'simParam/fobiExample/arcs_fobi.csv'
# # vnf
# chainsfile = 'bin/simParam/fobiExample/chain_fobi.csv'
# chainsfile = 'simParam/fobiExample/chain_fobi.csv'
# givenPatha = '../../../Demos/system/spark3/'
# src='127.0.0.1'
# sinkNode = '127.0.0.1'
# srcApp = ['./ica_readModule.py','./ica_readModule2.py']#[list(apps_set)[0]]


''''WCNC Fobi Example'''
'''Example Fobi'''

nodesfile = 'bin/simParam/fobiExample/nodeSim_distfobi.csv'
nodesfile = 'simParam/fobiExample/nodeSim_distfobi.csv'
# component
# appSim
appSimFile = 'bin/simParam/fobiExample/appsim_fobi.csv'
appSimFile = 'simParam/fobiExample/appsim_fobi.csv'
# edges
arcsfile = 'bin/simParam/fobiExample/arcs_distfobi.csv'
arcsfile = 'simParam/fobiExample/arcs_distfobi.csv'
# vnf
chainsfile = 'bin/simParam/fobiExample/chain_fobi.csv'
chainsfile = 'simParam/fobiExample/chain_fobi.csv'
givenPatha = 'Demos/system/fobi/'
src='10.0.1.14'
sinkNode = '10.0.1.12'
srcApp = ['./ica_readModule.py','./ica_readModule2.py']#[list(apps_set)[0]]

#
# #
# nodesfile = 'simParam/dummyExample/nodeSim_0'+ '.csv'
# # component
# appsfile = 'simParam/dummyExample/sim_' + str(trialx) + '.csv'
# # appSim
# appSimFile = 'simParam/dummyExample/appsim_1'+'.csv'
# # edges
# arcsfile = 'simParam/dummyExample/arcs_0' + '.csv'
# # vnf
# chainsfile = 'simParam/dummyExample/chain_' + str(1) + '.csv'


###load concrete parameters
# vnf data
chain_data = pandas.read_csv(chainsfile)
# node data
node_data = pandas.read_csv(nodesfile)
node_data['Node']= node_data['Node'].astype(str)
# component data
# appsfile_data = pandas.read_csv(appsfile).sort_values(by='quality', ascending=[False])
appsfile_data = pandas.read_csv(appSimFile)
# appPort data
appPort_data = pandas.read_csv(appSimFile)
# edges data
arc_data = pandas.read_csv(arcsfile)
arc_data[['Start','End']] = arc_data[['Start','End']].astype(str)
###convert data into indexed set
# node set
node_data.set_index(['Node'], inplace=True)
#node_data.sort_index(inplace=True)
# vnf set
chain_data.set_index(['srcapp', 'srcport','dstapp'], inplace=True)
chain_data.sort_index(inplace=True)
# appPort
appPort_data.set_index(['srcapp', 'port'], inplace=True)
appPort_data.sort_index(inplace=True)
# arc_data.rename(index= lambda x: str(x))
# component set
# appsfile_data.set_index(['App'], inplace=True)
appsfile_data.set_index(['srcapp'], inplace=True)
# edge set
arc_data.set_index(['Start', 'End'], inplace=True)
#arc_data.sort_index(inplace=True)

#extract indicies from data
# node index
node_set = node_data.index.unique()
node_set = [str(i) for i in node_set]
#print node_set ,'*****************'
# edge index
arc_set = list(arc_data.index.unique())
arc_set = [(str(i[0]),str(i[1])) for i in arc_set]
# appPort index
appPort_set = appPort_data.index.unique()
dictParam = {}
dictExec = {}
for alg,port in appPort_set:
    dictParam[alg] = appPort_data.loc[(alg,port),'parameter']
    dictExec[alg]  = appPort_data.loc[(alg,port),'executable']
# chain index
chain_set = chain_data.index.unique()
chain_set = sorted(chain_set, key=lambda tup: tup[1])
# chain_set = [(1,2),(2,3),(3,2),(3,4)]
# component inex
apps_set = set(appsfile_data.index.unique())



trialx=0
SINRth=0.1
srcNode=src

mapping_set = {(list(apps_set)[0],src), (list(apps_set)[-1], sinkNode)}
#print mapping_set ,'*****************'

# sinkNode = list(node_set)[-1]
sinkApp = list(apps_set)[-1]
# srcApp = [list(apps_set)[0]]
sinkApp = './cov2svd.py'
srcAppList = srcApp
maxTimeslots = 3
timeslots_set = range(1, maxTimeslots + 1)
timeBound = 3
#timeslots_set = range(3, maxTimeslots + 1)
bigM = 1e6