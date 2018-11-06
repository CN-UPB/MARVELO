from pyomo.environ import *
from libex import generate_xml
import math
#import pyomo
import pandas
import logging
import time
import pickle
from configInput import *

model = ConcreteModel()
src ='4'
sinkNode='3'
trialx=0
SINRth=317
srcNode=src

##
''' Directories with concrete values'''
# node
nodesfile = 'bin/simParam/nodeSim_' + str(trialx) + '.csv'
# component
appsfile = 'bin/simParam/sim_' + str(trialx) + '.csv'
# appSim
appSimFile = 'bin/simParam/appsim_1'+'.csv'
# edges
arcsfile = 'bin/simParam/arcs_' + str(trialx) + '.csv'
# vnf
chainsfile = 'bin/simParam/chain_' + str(1) + '.csv'


nodesfile = 'simParam/dummyExample/nodeSim_0'+ '.csv'
# component
appsfile = 'simParam/dummyExample/sim_' + str(trialx) + '.csv'
# appSim
appSimFile = 'simParam/dummyExample/appsim_1'+'.csv'
# edges
arcsfile = 'simParam/dummyExample/arcs_0' + '.csv'
# vnf
chainsfile = 'simParam/dummyExample/chain_' + str(1) + '.csv'

'''load concrete parameters Do not change this'''
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

'''convert data into indexed set'''
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

'''extract indicies from data'''
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

'''Other concrete paramaeters'''
## predefined mapping: {(1, 'A'), (5, 'E')} {src,dest}, of course can be extended to mulitple source (with component '1')
#mapping_set = {(list(apps_set)[0], list(node_set)[0]), (list(apps_set)[-1], list(node_set)[-1])}
mapping_set = {(list(apps_set)[0],src), (list(apps_set)[-1], sinkNode)}
# sinkNode = list(node_set)[-1]
sinkApp = list(apps_set)[-1]
srcApp = list(apps_set)[0]
maxTimeslots = 17
timeslots_set = range(1, maxTimeslots + 1)
timeBound = 3
#timeslots_set = range(3, maxTimeslots + 1)
bigM = 1e6
#SINRth = 2
#model.SINRth = 1.5
model.noise = 0.000019

''' Intializing model sets'''
model.nodes = Set(initialize=node_set)
model.components = Set(initialize=apps_set)
model.appPorts = Set( initialize=appPort_set, dimen=2)
model.timeslots = Set(initialize=timeslots_set)
model.vnf = Set(initialize=chain_set, dimen=3)
model.edges = Set(initialize=arc_set, dimen=2)
model.mapping = Set(initialize=mapping_set, dimen=2)

''''Variables'''
model.usedTimeslots = Var(model.timeslots, within=Boolean)
model.map = Var(model.appPorts * model.nodes, within=Boolean)
model.theta = Var(model.nodes*model.components, within=Boolean)
model.fwdNode = Var(model.appPorts*model.nodes*model.timeslots, within = Boolean)
model.schedule = Var(model.appPorts*model.nodes*model.nodes * model.timeslots, domain=Boolean)
model.h = Var(model.appPorts*model.nodes*model.nodes,domain= NonNegativeIntegers)
model.z =Var(model.edges*model.timeslots,domain= NonNegativeReals)


#### Intialize values ######
for i in model.h:
        print i
        model.h[i].value=0
# #
for i in model.schedule:
    model.schedule[i].value = 0

for i in model.map:
    model.map[i].value = 0

############################################################
# Constraints
############################################################
## reduce map to theta
######################
def uppertheta(model,node,app):
    #print 'checking', node,app
    #print '----', [for i]
    return bigM*model.theta[node,app]>=sum([model.map[i] for i in model.map if i[0]==app and i[2]==node])
model.uppertheta = Constraint(model.nodes,model.components,rule =uppertheta)

def lowertheta(model,node,app):
    return model.theta[node,app]<=sum([model.map[i] for i in model.map if i[0]==app and i[2]==node])
model.lowertheta = Constraint(model.nodes,model.components,rule =lowertheta)

## relaxation using z
######################
def sandZlowLimit(model,node1,node2,timeslot):
    return model.z[node1,node2,timeslot] >=0
model.sandZlowLimit = Constraint(model.edges,model.timeslots,rule =sandZlowLimit)

def sandZupLimit(model, node1,node2,timeslot):
    edgeActive = sum([model.schedule[a, node1,node2, timeslot] for a in model.appPorts])
    return model.z[node1,node2,timeslot] <=edgeActive*(len(model.appPorts)*len(model.nodes)-1)
model.sandZupLimit = Constraint(model.edges,model.timeslots,rule=sandZupLimit)

def sandFlowLimit(model,node1,node2,timeslot):
    edgeActive = sum([model.schedule[a, node1,node2, timeslot] for a in model.appPorts])
    interference = sum(sum(
        model.fwdNode[c, v, timeslot] * arc_data.ix[(int(v), int(node2)), 'Attenuation']for
        v in model.nodes if v != node1 and v != node2)
                       for c in model.appPorts)
    return model.z[node1,node2,timeslot] >= interference - (len(model.appPorts)*len(model.nodes)-1)*(1-edgeActive)
model.sandFlowLimit = Constraint(model.edges,model.timeslots,rule=sandFlowLimit)

def sandFupLimit(model,node1,node2,timeslot):
    interference = sum(sum(
        model.fwdNode[c, v, timeslot]* arc_data.ix[(int(v), int(node2)), 'Attenuation']
                   for v in model.nodes if v != node1 and v != node2)
                       for c in model.appPorts)
    return model.z[node1,node2,timeslot]<=interference
model.sandFupLimit = Constraint(model.edges,model.timeslots,rule=sandFupLimit)


##Placement Constraints
############################################################
''' every component needs to be mapped only once to a node
 special treatment for compnents that have predefined mappings'''


def componentIsMapped(model, component,portNr):
    premapped = filter(lambda x: x[0] == component, model.mapping)
    if premapped:
         print 'premapping:\n' ,premapped
         #print component, portNr, premapped[0][1]
         model.map[component,portNr, premapped[0][1]].value = 1
         model.map[component, portNr,premapped[0][1]].fixed = True
    return sum([model.map[component,portNr, n] for n in model.nodes]) == 1

model.componentIsMapped = Constraint(model.appPorts, rule=componentIsMapped)


'''A node is not overutilized by the number of running instances '''

# def capacityConstraintConcrete(model, node):
#     return sum(model.map[c, node] * list(appsfile_data.ix[c]['demand'])[0] for c in model.components) <= node_data.ix[
#         node, 'capacity']
def capacityConstraintConcrete(model, node):
    return sum(model.map[c, node] * appPort_data.ix[c]['demand'] for c in model.appPorts) <= node_data.ix[
        int(node), 'capacity']
model.capacityConstraint = Constraint(model.nodes, rule=capacityConstraintConcrete)

# # every component needs to be mapped to at MOST one  node
def componentMappedAtMostOnce(model, component,port):
    return sum([model.map[component,port, n] for n in model.nodes]) <= 1
#model.componentMappedAtMostOnce = Constraint(model.appPorts, rule=componentMappedAtMostOnce)

# different ports for the same app are placed on the same node
#
def portsAttachedToApps(model,app1,port1,app2,port2,node):
    if app1 == app2:
        return model.map[app1,port1,node] == model.map[app2,port2,node]
    return Constraint.Skip
model.portsAttachedToApps = Constraint(model.appPorts,model.appPorts,model.nodes, rule = portsAttachedToApps)

### Duplex Constraints'''
############################################################

'''in one timeslot, a node cannot send and receive simultaneously'''

#updated
def noDuplex(model, node, timeslot):
    incomingedges = filter(lambda x: x[1] == node, model.edges)

    return (sum([model.fwdNode[c,node, timeslot] for c in model.appPorts]) + sum(
        [model.schedule[c,e,timeslot] for e in incomingedges for c in model.appPorts])) <= 1

model.nuDuplex = Constraint(model.nodes, model.timeslots, rule=noDuplex)



# Forwarding constraints
############################################################


''' A node must send a vnf, only if it received the previous instance(s) in the chain or received the vnf '''
def flowControl(model,component,port,node):
    #print 'checking flow control\n',component,port,node
    if component == srcApp and node == src:
            succ_p = filter(lambda x: (x[0] == component and x[1]==port), model.vnf)
            outgoing = filter(lambda x: x[0] == node, model.edges)
            outgoing.append((node,node))
            return sum(model.h[component,port,e] for e in outgoing )-model.map[component,port,node]*len(succ_p)==0

    elif component == sinkApp and node == sinkNode:
            preds_p =filter(lambda x: x[2] == component, model.vnf)
            incoming = filter(lambda x: x[1] == node, model.edges)
            incoming.append((node, node))

            return sum(model.h[c[0],c[1],e] for c in preds_p for e in incoming )-model.map[component,port,node]*len(preds_p)>=0 # for loop placement
    else:
        succ_p = filter(lambda x: (x[0] == component and x[1]==port), model.vnf)
        preds_p = filter(lambda x: x[2] == component, model.vnf)
        outgoing = filter(lambda x: x[0] == node, model.edges)
        outgoing.append((node, node))

        incoming = filter(lambda x: x[1] == node, model.edges)
        incoming.append((node, node))

        return sum(model.h[component,port,e] for e in outgoing )-model.map[component,port,node]*len(succ_p) == sum(model.h[component,port,e] for e in incoming )-sum(model.theta[node,c[2]]  for c in succ_p)
model.flowControl = Constraint(model.appPorts, model.nodes, rule=flowControl)

def mapAndH(model,component,port,node):
    succ_p = filter(lambda x: (x[0] == component and x[1] == port), model.vnf)
    outgoing = filter(lambda x: x[0] == node, model.edges)
    outgoing.append((node, node))
    if component!= sinkApp:
        return model.map[component,port,node]*len(succ_p) - sum(model.h[component,port,e] for e in outgoing) == 0
    #else: sinkApp
    return model.map[component, port, node]*len(succ_p) - sum(model.h[component, port, e] for e in outgoing) == 0

    # preds_p = filter(lambda x: x[2] == component, model.vnf)
    # incoming = filter(lambda x: x[1] == node, model.edges)
    # incoming.append((node, node))
    # return sum(model.h[c[0],c[1], e] for e in incoming for c in preds_p) - model.map[component,port,node] >=0
    #return Constraint.Skip
model.mapAndH = Constraint(model.appPorts, model.nodes, rule=mapAndH)

'''for every timeslot and every active, we need to check SINR constraint'''

#update
def SINR(model, source, destination, timeslot):
    edge = (source, destination)

    edgeActive = sum([model.schedule[ a,edge, timeslot]  for a in model.appPorts])

    # do serious checking:


    signal = arc_data.ix[(int(source), int(destination)), 'Attenuation']

    # compute interference:
    # interference = sum(sum(
    #     model.fwdNode[c, v, timeslot] * arc_data.ix[(v, destination), 'Attenuation'] for
    #     v in model.nodes if v != source and v != destination)
    #                    for c in model.appPorts)


    # return edgeActive * signal >= edgeActive * (interference + model.noise)*model.SINRth
    return edgeActive * signal >=  ((model.z[edge,timeslot] +edgeActive*model.noise)*SINRth)


model.SINR = Constraint(model.edges, model.timeslots, rule=SINR)



def printSINR(model, source, destination, timeslot):
    edge = (source, destination)
    edgeActive = sum([model.schedule[ a,edge, timeslot].value  for a in model.appPorts])
    signal = arc_data.ix[(source, destination), 'Attenuation']
    interference = sum(sum(
        model.fwdNode[c, v, timeslot].value * arc_data.ix[(v, destination), 'Attenuation'] for
        v in model.nodes if v != source and v != destination)
                       for c in model.appPorts)
    print edgeActive * signal /  (interference +edgeActive*model.noise)
# Variable dependency
############################################################
'''define the relationship between schedule and map'''

'''Map is checking if it receives the required vnf in the chain'''



def fwdNodeUp (model,node,component,port,timeslot):
    outgoingedges = filter(lambda x: x[0] == node, model.edges)
    #outgoingedges.append((node, node))
    return model.fwdNode[component,port,node,timeslot] - sum(model.schedule[component,port,e,timeslot] for e in outgoingedges )<=0

model.fwdNodeUp = Constraint(model.nodes, model.appPorts, model.timeslots, rule=fwdNodeUp)


def fwdNodeDown (model,node,component,port,timeslot):
    outgoingedges = filter(lambda x: x[0] == node, model.edges)
    #outgoingedges.append((node, node))
    return bigM*model.fwdNode[component,port,node,timeslot] - sum(model.schedule[component,port,e,timeslot] for e in outgoingedges )>=0

model.fwdNodeDown = Constraint(model.nodes, model.appPorts, model.timeslots, rule=fwdNodeDown)


def SandHup(model,component,port,node1,node2):
    return model.h[component,port,node1,node2] - sum(model.schedule[component,port,node1,node2,t] for t in model.timeslots) >=0
model.SandHup = Constraint( model.appPorts,model.nodes,model.nodes, rule=SandHup)


def SandHdown(model,component,port,node1,node2):
    return model.h[component,port,node1,node2] - bigM*sum(model.schedule[component,port,node1,node2,t] for t in model.timeslots) <=0
model.SandHdown = Constraint( model.appPorts,model.nodes,model.nodes, rule=SandHdown)



'''force non-usage of a timeslot'''


def timeScheduleDown(model, timeslot):  # can be removed for minimize timeslots objective
    return sum([model.schedule[a, e, timeslot] for e in model.edges for a in model.appPorts]) - model.usedTimeslots[
        timeslot] >= 0
model.timeScheduleDown = Constraint(model.timeslots, rule=timeScheduleDown)

'''force usage of a timeslot'''
def timeScheduleUp(model, timeslot):
    return sum([model.schedule[a, e, timeslot] for e in model.edges for a in model.appPorts]) - bigM * \
                                                                                                model.usedTimeslots[
                                                                                                    timeslot] <= 0
model.timeScheduleUp = Constraint(model.timeslots, rule=timeScheduleUp)


def timeScheduleOrder(model, timeslot):
    if timeslot > timeslots_set[0]:
        return model.usedTimeslots[timeslot] <= model.usedTimeslots[timeslot - 1]
    return Constraint.Skip
model.timeScheduleOrder = Constraint(model.timeslots, rule=timeScheduleOrder)



#########
# Tracking the flow
#########


############################################################
# Objetives
############################################################

# example 1: minimize number of timeslots?
# def objfn():
#     return sum(model.usedTimeslots[i] for i in model.timeslots) + sum([[1e-3*model.z[i].value
model.obj = Objective(expr=sum(model.usedTimeslots[i] for i in model.timeslots) -0.01*sum(model.schedule[i] for i in model.schedule))


############################################################
# Solver
############################################################
def solve(m):
    """Solve the model."""
    solver = pyomo.opt.SolverFactory('gurobi')

    # start_time2 = time.clock()
    results = solver.solve(m, tee=False, keepfiles=False)
    # endTimeOpt2= (time.clock()-start_time2)
    if (results.solver.status != pyomo.opt.SolverStatus.ok):
        logging.warning('Check solver not ok?')
    if (results.solver.termination_condition != pyomo.opt.TerminationCondition.optimal):
        logging.warning('Check solver optimality?')
    #return results


############################################################
# Only dbugging
############################################################


#
# for i in model.h:
#         if model.h[i].value==0:
#             model.h[i].fixed = True
#
# for i in model.schedule:
#     if model.schedule[i].value == 0:
#         model.schedule[i].fixed = True
#
# for i in model.map:
#     if model.map[i].value == 0:
#         model.map[i].fixed = True


def calcBER(s,f):
    p_noError =1
    uTS = [set([i[-1] for i in s if s[2]!=s[3]])]
    ss = [i for i in s if i[3]!=i[2]]
    for sig in ss:
        print sig
        interference = sum(
            arc_data.ix[(fwd[0], fwd[1]), 'Attenuation']
            for fwd in f if fwd[-1]==sig[-1] and fwd[1] == sig[3] and fwd[0] != sig[2] and fwd[0] != sig[3])
        s_to_n  = arc_data.ix[(sig[2], sig[3]), 'Attenuation']/(interference+0.000019)
        print 'snr = ',s_to_n
        ser = math.erfc(s_to_n**0.5 * math.sin(3.14/32))
        p_SymbError = 1- p_noError*(1-ser)
    return p_SymbError

def saveVar(varName,filename):
   # with open('bin/results/'+filename,"wb") as f:
        with open('results/' + filename, "wb") as f:
            pickle.dump( varName, f)

def loadVar(filename):
        return pickle.load(open('results/'+filename, "rb"))
start_time_model = time.time()
timeElapsed = solve(model)
timeElapsed = time.time() - start_time_model
# srcNode= [i for i in model.mapping][0][1]
try:
    print 'mapping follows (component, node): \n', [i[0::2] for i in model.map if model.map[i] == 1], '\n'
    #print 'Active Edges (src,dst,timeslot) are:\n', [(i[0:2],i[-1]) for i in model.schedule if model.schedule[i] == 1 and i[0]!=i[1]], '\n'
    #print 'Scheduler follows \n', [i for i in model.schedule if model.schedule[i] == 1 if i[2] != i[3]]
    #print 'All paths within Scheduler follows \n', [i for i in model.schedule if model.schedule[i] == 1]
    #print 'saving file name: ' + str(len(node_set)) + str(trialx)
    print 'Elapsed time for the optimization model: ', timeElapsed
    # print 'Saving file: ','OptSource' + str(len(node_set))+'SINR'+str(SINRth) + 'T'+ str(trialx)
    saveVar({'time': timeElapsed,
             'number':sum(model.usedTimeslots[i].value for i in model.timeslots),
             's':[i for i in model.schedule if model.schedule[i].value ==1],
             'f':[i for i in model.fwdNode if model.fwdNode[i].value > 0.9], 'map':[i for i in model.map if model.map[i].value >0.9]}, 'OptSource' + str(len(node_set)) +'SINR'+str(SINRth) + 'T'+ str(trialx)+ '.pickle')
    # for i in model.schedule:
    #     if model.schedule[i].value ==1 and i[2]!=i[3]:
    #         printSINR(model, i[2], i[3], i[-1])
    # print calcBER([i for i in model.schedule if model.schedule[i].value > 0.9],
    #                 [i for i in model.fwdNode if model.fwdNode[i].value > 0.9])
    # for i in model.map:
    #       if model.map[i].value >0.9:
    #           print 'model.map[',i,'].value = 1'
    #           print 'model.map[', i, '].fixed = True'
    # print '**** h ****'
    # for i in model.h:
    #       if model.h[i].value >0.9:
    #           print 'model.h[',i,'].value = ',model.h[i].value
    #           print 'model.h[', i, '].fixed = True'
    # print '\n******* routing *******\n', [j for j in model.schedule if model.schedule[j].value>=0.9]
    # for i in model.schedule:
    #       if model.schedule[i].value >=0.9:
    #           print 'model.schedule[',i,'].value = 1'
    #           print 'model.schedule[',i,'].fixed = True'
    # us =  list(set([i[4] for i in model.schedule if model.schedule[i].value == 1 and i[2] != i[3]]))
    # print '** used trans = ', set([i for i in model.schedule if model.schedule[i].value == 1 and i[2] != i[3] and i[4]==us[-1]] )
    # print '\n******* routing *******\n', [j for j in model.schedule if model.schedule[j].value>=0.9]
except:
    saveVar({'time': timeElapsed, 'number': 'failed'}, 'OptSource' + str(src) + str(len(node_set)) + str(trialx)+ '.pickle')
    print 'Failed to find solution'

r_o = []
for i in model.schedule:
    if model.schedule[i].value >=0.9:
        r_o.append(i[:-1])
r = set(r_o)
print "to XML"
for o in r:
    print o
generate_xml(model.schedule,model.theta,model.vnf,[srcApp],sinkApp,sinkNode)
