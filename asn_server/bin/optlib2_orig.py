from pyomo.environ import *
from libex import generate_xml
import math
#import pyomo
import pandas
import logging
import time
import pickle
from configInput import *
import os

model = ConcreteModel()

#print os.environ["PATH"]


def optimizeAllocation():
       # nodesfile = 'simParam/nodeSim_' + str(trialx) + '.csv'
       # # component
       # appsfile = 'simParam/sim_' + str(trialx) + '.csv'
       # # appSim
       # appSimFile = 'simParam/appsim_11'+'.csv'
       # # edges
       # arcsfile = 'simParam/arcs_' + str(trialx) + '.csv'
       # # vnf
       # chainsfile = 'simParam/chain_' + str(1) + '.csv'

       # '''load concrete parameters'''
       # # vnf data
       # chain_data = pandas.read_csv(chainsfile)
       # # node data
       # node_data = pandas.read_csv(nodesfile)
       # # component data
       # # appsfile_data = pandas.read_csv(appsfile).sort_values(by='quality', ascending=[False])
       # appsfile_data = pandas.read_csv(appSimFile)
       # # appPort data
       # appPort_data = pandas.read_csv(appSimFile)
       # # edges data
       # arc_data = pandas.read_csv(arcsfile)
       #
       #
       # '''convert data into indexed set'''
       # # node set
       # node_data.set_index(['Node'], inplace=True)
       # node_data.sort_index(inplace=True)
       # # vnf set
       # chain_data.set_index(['srcapp', 'srcport','dstapp'], inplace=True)
       # chain_data.sort_index(inplace=True)
       # # appPort
       # appPort_data.set_index(['srcapp', 'port'], inplace=True)
       # appPort_data.sort_index(inplace=True)
       # # component set
       # # appsfile_data.set_index(['App'], inplace=True)
       # appsfile_data.set_index(['srcapp'], inplace=True)
       # # edge set
       # arc_data.set_index(['Start', 'End'], inplace=True)
       # arc_data.sort_index(inplace=True)
       #
       # '''extract indicies from data'''
       # # node index
       # node_set = node_data.index.unique()
       # node_set = [str(i) for i in node_set]
       # # edge index
       # arc_set = list(arc_data.index.unique())
       # arc_set = [(str(i[0]),str(i[1])) for i in arc_set]
       # # appPort index
       # appPort_set = appPort_data.index.unique()
       # # chain index
       # chain_set = chain_data.index.unique()
       # chain_set = sorted(chain_set, key=lambda tup: tup[1])
       # # chain_set = [(1,2),(2,3),(3,2),(3,4)]
       # # component inex
       # apps_set = set(appsfile_data.index.unique())

       '''Other concrete paramaeters'''
       ## predefined mapping: {(1, 'A'), (5, 'E')} {src,dest}, of course can be extended to mulitple source (with component '1')
       #mapping_set = {(list(apps_set)[0], list(node_set)[0]), (list(apps_set)[-1], list(node_set)[-1])}
       # sinkNode = list(node_set)[-1]
       # src = '127.0.0.1'
       # sinkNode = '127.0.0.1'
       # SINRth = 317
       # srcNode = '127.0.0.1'
       # sinkApp = './cov2svd.py'#list(apps_set)[-1]
       # srcApp = './ica_readModule2.py'#list(apps_set)[0]
       # srcApp2 = './ica_readModule.py'#list(apps_set)[0]
       # mapping_set = {(srcApp,src), (srcApp2,src),(sinkApp, sinkNode)}#{(list(apps_set)[0],src), (list(apps_set)[-1], sinkNode)}
       #
       # maxTimeslots = 1
       # timeslots_set = range(1, maxTimeslots + 1)
       # timeBound = 3
       # #timeslots_set = range(3, maxTimeslots + 1)
       # bigM = 1e6
       # #SINRth = 2
       # #model.SINRth = 1.5
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
       # print '*** values of theta ***'

       for i in model.h:
               #print i
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
               model.fwdNode[c, v, timeslot] * arc_data.ix[((v), (node2)), 'Attenuation']for
               v in model.nodes if v != node1 and v != node2)
                              for c in model.appPorts)
           return model.z[node1,node2,timeslot] >= interference - (len(model.appPorts)*len(model.nodes)-1)*(1-edgeActive)
       model.sandFlowLimit = Constraint(model.edges,model.timeslots,rule=sandFlowLimit)

       def sandFupLimit(model,node1,node2,timeslot):
           interference = sum(sum(
               model.fwdNode[c, v, timeslot]* arc_data.ix[((v), (node2)), 'Attenuation']
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
               node, 'capacity']
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
           if (component in srcAppList ) and node == src:
                   succ_p = filter(lambda x: (x[0] == component and x[1]==port), model.vnf)
                   outgoing = filter(lambda x: x[0] == node, model.edges)
                   outgoing.append((node,node))
                   return sum(model.h[component,port,e] for e in outgoing )-model.map[component,port,node]*len(succ_p)==0

           elif component == sinkApp and node == sinkNode:
                   preds_p =filter(lambda x: x[2] == component, model.vnf)
                   incoming = filter(lambda x: x[1] == node, model.edges)
                   incoming.append((node, node))

                   return sum(model.h[c[0],c[1],e] for c in preds_p for e in incoming )-model.map[component,port,node]*len(preds_p)==0 # for loop placement
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


           signal = arc_data.ix[((source), (destination)), 'Attenuation']

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
           with open('bin/results/'+filename,"wb") as f:
           #   with open('results/' + filename, "wb") as f:
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
           print 'Scheduler follows \n'
           s_debug = [i for i in model.schedule if model.schedule[i] == 1 if i[2] != i[3]]
           for i in s_debug:
               print i
           #print 'All paths within Scheduler follows \n', [i for i in model.schedule if model.schedule[i] == 1]
           #print 'saving file name: ' + str(len(node_set)) + str(trialx)
           print 'Elapsed time for the optimization model: ', timeElapsed
           # print 'Saving file: ','OptSource' + str(len(node_set))+'SINR'+str(SINRth) + 'T'+ str(trialx)
           # saveVar({'time': timeElapsed,
           #          'number':sum(model.usedTimeslots[i].value for i in model.timeslots),
           #          's':[i for i in model.schedule if model.schedule[i].value ==1],
           #          'f':[i for i in model.fwdNode if model.fwdNode[i].value > 0.9], 'map':[i for i in model.map if model.map[i].value >0.9]}, 'OptSource' + str(len(node_set)) +'SINR'+str(SINRth) + 'T'+ str(trialx)+ '.pickle')
           # # for i in model.schedule:
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
           #saveVar({'time': timeElapsed, 'number': 'failed'}, 'OptSource' + sgitr(src) + str(len(node_set)) + str(trialx)+ '.pickle')
           print 'Failed to find solution'
       r_o = []
       for i in model.schedule:
           if model.schedule[i].value >= 0.9:
               r_o.append(i[:-1])
       r = set(r_o)
       #print "to XML"
       #for o in r:
       #    print o
       #print '*******', givenPatha
       generate_xml(model.schedule,model.theta,model.vnf,srcAppList,sinkApp,sinkNode,dictParam,givenPatha)

def heuristicAllocation():
    import math
    import time
    import pandas
    import copy
    import itertools
    import pickle
    import sys
    #print srcAppList,sinkApp,chain_set
    #
    # # graph = {'A': ['B', 'C'], 'B': ['C', 'D'], 'C': ['D'], 'D': ['C'], 'E': ['F'], 'F': ['C']}
    #
    # # trialx =0
    # # nr_nodes = 9
    # # nr_apps = 5
    # # topology='linear'
    # # sourcenode = 'E'#sourcenode
    # # sinkNode = 'D'#sinkNode
    # # No= 0.000019
    # # nodeCapacity=21
    # # SINRth = 1
    #
    # # print nr_nodes, nr_apps, topology, sourcenode, sinkNode, SINRth
    #
    # #
    # srcNode = sourcenode
    # endNode = sinkNode
    No = 1e-6
    errMargin = 1e-15
    powerControl = False#True

    # SINRth = SINRth - errMargin
    #
    # ''' Directories with concrete values'''
    #
    # # node
    # appsfile = 'simParam/sim_N' + str(nr_nodes) + '.csv'
    # nodesfile = 'simParam/nodeSim_N' + str(nr_nodes) + '.csv'
    # arcsfile = 'simParam/arcs_N' + str(nr_nodes) + '.csv'
    # appSimFile = 'simParam/appsim_' + str(nr_apps) + '.csv'
    # if topology == 'parallel':
    #     chainsfile = 'simParam/chain_parallel_' + str(nr_apps)
    # elif topology == 'linear':
    #     chainsfile = 'simParam/chain_linear_' + str(nr_apps)
    #
    # '''load concrete parameters'''
    # # vnf data
    # chain_data = pandas.read_csv(chainsfile)
    # # node data
    # node_data = pandas.read_csv(nodesfile)
    # # component data
    # # appsfile_data = pandas.read_csv(appsfile).sort_values(by='quality', ascending=[False])
    # appsfile_data = pandas.read_csv(appSimFile)
    # # appPort data
    # appPort_data = pandas.read_csv(appSimFile)
    # # edges data
    # arc_data = pandas.read_csv(arcsfile)
    #
    # '''convert data into indexed set'''
    # # node set
    # node_data.set_index(['Node'], inplace=True)
    # node_data.sort_index(inplace=True)
    # # vnf set
    # chain_data.set_index(['srcapp', 'srcport', 'dstapp'], inplace=True)
    # chain_data.sort_index(inplace=True)
    # # appPort
    # appPort_data.set_index(['srcapp', 'port'], inplace=True)
    # appPort_data.sort_index(inplace=True)
    # # component set
    # # appsfile_data.set_index(['App'], inplace=True)
    # appsfile_data.set_index(['srcapp'], inplace=True)
    # # edge set
    # arc_data.set_index(['Start', 'End'], inplace=True)
    # arc_data.sort_index(inplace=True)
    #
    # '''extract indicies from data'''
    # # node index
    # node_set = list(node_data.index.unique())
    # # edge index
    # arc_set = list(arc_data.index.unique())
    # # appPort index
    # appPort_set = appPort_data.index.unique()
    # # chain index
    # chain_set = chain_data.index.unique()
    # chain_set = sorted(chain_set, key=lambda tup: tup[1])
    # capacityNode = {v: node_data.loc[v]['capacity'] for v in node_set}
    # # chain_set = [(1,2),(2,3),(3,2),(3,4)]
    # # component inex
    # apps_set = set(appsfile_data.index.unique())
    #
    # # capacityNode = {v:20 for v in node_set}
    capacityNode = {node:node_data.ix[node, 'capacity'] for node in node_set}
    # # print capacityNode
    #
    # startApp = list(appPort_set)[0]
    # endApp = list(appPort_set)[-1]
    # mapping_set = list({(startApp, srcNode), (endApp, endNode)})
    startApp  = srcApp
    endApp = sinkApp
    srcNode = src
    endNode = sinkNode
    ##### Generate a Graph ########


    t = [0]
    keysGraph = list(itertools.product(node_set, t))
    Graph = dict.fromkeys(list(keysGraph), [])
    for s, e in arc_set:
        oldValue = copy.copy(Graph[(s, 0)])
        oldValue.append((e, t[0]))
        Graph[(s, 0)] = oldValue

    origGraph = dict.fromkeys(list(node_set), [])
    for s, e in arc_set:
        oldValue = copy.copy(origGraph[(s)])
        oldValue.append((e))
        origGraph[(s)] = oldValue
    ###### Generate variables ######
    scho = {(i, j, b, tt): 0 for i in node_set for j in node_set for b in list(appPort_set) for tt in t}
    fwdo = {(i, tt): 0 for i in node_set for tt in t}
    fwdappo = {(v, b, tt): 0 for v in node_set for b in appPort_set for tt in t}
    txpwro = {i: 0 for i in node_set}

    mapf = {(app, v): 0 for app in apps_set for v in node_set}
    appT = (1, 1)

    ##### Functions ##########
    # + with shortest path
    def find_first_path(graph, start, end, appTriv, txpwr, sch_o, fwd, fwdapp, path=[], searchRange=4):
        # t= start[-1]
        sch = sch_o
        pathTemp = path + [start]
        pathNodes = [i[0] for i in pathTemp]
        if start[0] == end:
            sch[start[0], start[0], appTriv, start[-1]] = 1
            updateFWD(sch, fwd, txpwr)
            updateFWDApp(sch, fwdapp)
            path = path + [[start[0], start[-1]]]
            removeFromSch(path, sch, fwd, fwdapp, txpwr, appTriv)
            mon = [i for i in sch if sch[i] == 1]

            return path, sch
        path = pathTemp
        # if not graph.has_key(start):
        #     return None
        reversable = False
        shortest = None
        shortestSch = sch
        mon = [i for i in sch if sch[i] == 1]

        for node in origGraph[start[0]]:
            t = start[-1]
            node = [node, start[-1]]
            if node[0] not in pathNodes:
                if sch[start[0], node[0], appTriv, start[1]] != 1:
                    sch[start[0], node[0], appTriv, start[1]] = 1
                    reversable = True
                    updateFWD(sch, fwd, txpwr)
                    updateFWDApp(sch, fwdapp)
                    mon = [i for i in sch if sch[i] == 1]

                    if not checkDuplex(sch, fwd, fwdapp) or not checkSINR_v2(start[0], node[0], appTriv, start[1],
                                                                             txpwr, fwd):
                        if reversable:
                            sch[start[0], node[0], appTriv, start[1]] = 0
                            updateFWD(sch, fwd, txpwr)
                            updateFWDApp(sch, fwdapp)
                            reversable = False
                            mon = [i for i in sch if sch[i] == 1]

                        timeSlots = list(set([i[-1] for i in sch]))
                        fwdFlag = False
                        while not fwdFlag:
                            for t in timeSlots:
                                # if t==3:
                                #     print'debughere'
                                if sch[start[0], node[0], appTriv, t] != 1:
                                    sch[start[0], node[0], appTriv, t] = 1
                                    updateFWD(sch, fwd, txpwr)
                                    updateFWDApp(sch, fwdapp)
                                    mon = [i for i in sch if sch[i] == 1]

                                    reversable = True

                                    if (not checkDuplex(sch, fwd, fwdapp) or not checkSINR_v2(start[0], node[0],
                                                                                              appTriv, t, txpwr,
                                                                                              fwd)) and reversable:
                                        sch[start[0], node[0], appTriv, t] = 0
                                        updateFWD(sch, fwd, txpwr)
                                        updateFWDApp(sch, fwdapp)
                                        mon = [i for i in sch if sch[i] == 1]

                                    else:
                                        fwdFlag = True
                                        node = (node[0], t)
                                        mon = [i for i in sch if sch[i] == 1]

                                        break
                            if not fwdFlag:
                                addTimeSlot(sch, fwdapp)
                                timeSlots = list(set(i[-1] for i in graph.keys()))
                                #print timeSlots
                                t = timeSlots[-1]
                                sch[start[0], node[0], appTriv, timeSlots[-1]] = 1
                                updateFWD(sch, fwd, txpwr)
                                updateFWDApp(sch, fwdapp)
                                mon = [i for i in sch if sch[i] == 1]

                                if (not checkDuplex(sch, fwd, fwdapp) or not checkSINR_v2(start[0], node[0], appTriv,
                                                                                          timeSlots[-1], txpwr,
                                                                                          fwd)) and reversable:
                                    checkSINR_v2(start[0], node[0], appTriv,
                                                 timeSlots[-1], txpwr,
                                                 fwd)
                                    sch[start[0], node[0], appTriv, t] = 0
                                    updateFWD(sch, fwd, txpwr)
                                    updateFWDApp(sch, txpwr)
                                    mon = [i for i in sch if sch[i] == 1]
                                    print 'debugHere'
                                else:
                                    break
                                # oldSlots =list(set([i[-1] for i in sch]))
                                # timeSlots = oldSlots + [len(oldSlots)]
                    # path = path + [[start[0],t]]
                    # print path
                    if searchRange > 0:
                        searchRange = searchRange - 1
                        lastnode = list(path[-1])
                        lastnode[-1] = t
                        path[-1] = tuple(lastnode)
                        #print 1,node
                        newpath, sch = find_first_path(graph, node, end, appTriv, txpwr, sch, fwd, fwdapp, path,
                                                       searchRange)
                        if newpath:
                            if not shortest or len(set([i[1] for i in newpath])) < len(set(i[1] for i in shortest)):
                                shortest = newpath
                                shortestSch = sch
                                removeFromSch(shortest, sch, fwd, fwdapp, txpwr, appTriv)
                                #print shortest
                            removeFromSch(newpath, sch, fwd, fwdapp, txpwr, appTriv)
                    else:
                        path = path + [(node[0], node[1])]
                        removeFromSch(path, sch, fwd, fwdapp, txpwr, appTriv)
                        break

        return shortest, shortestSch
        # return None

    def removeFromSch(pathToRemove, sch, fwd, fwdapp, txpwr, appTriv, extraSearch=True):
        if len(pathToRemove) >= 2:
            for p in range(0, len(pathToRemove) - 1, 1):
                if pathToRemove[p][0] != pathToRemove[p + 1][0]:
                    sch[pathToRemove[p][0], pathToRemove[p + 1][0], appTriv, pathToRemove[p][1]] = 0
                    updateFWD(sch, fwd, txpwr)
                    updateFWDApp(sch, fwdapp)
        if extraSearch:
            for i in sch:
                if i[2] == appTriv:
                    sch[i] = 0

    def addToSch(pathToAdd, sch, appTriv, extraSearch=True):
        if len(pathToAdd) >= 2:
            for p in range(0, len(pathToAdd) - 1, 2):
                # if  pathToAdd[p][0]!= pathToAdd[p+1][0]:
                portDest = [l[1] for l in chain_set if l[0] == appTriv]
                if portDest:
                    portDest = portDest[0]
                else:
                    portDest = 1
                sch[pathToAdd[p][0], pathToAdd[p + 1][0], (appTriv, portDest), pathToAdd[p + 1][1]] = 1
                updateFWD(sch, fwdo, txpwro)
                updateFWDApp(sch, fwdappo)

    def updateFWD(sch, fwd, txpwr):
        timeslots = set([t[-1] for t in sch])
        for t in timeslots:
            for v in node_set:
                if sum(sch[i] for i in sch if i[-1] == t and i[0] == v and i[0] != i[1]) > 0:
                    # if  t==0:
                    #     print  'debughere',v
                    fwd[v, t] = 1
                    if txpwr[v] == 0:
                        txpwr[v] = 1 + errMargin

                else:
                    fwd[v, t] = 0
                    if sum(fwd[i] for i in fwd if i[0] == v) == 0:
                        txpwr[v] = 0

    def updateFWDApp(sch, fwdapp):
        timeslots = set([t[-1] for t in sch])
        for tu in timeslots:
            for v in node_set:
                for b in appPort_set:
                    # if v == 'B'  and b==(2,1)and (tu == 0 or tu ==2) and sum(sch[i] for i in sch if  i[0]==v and v!=i[1] and i[2] == b and i[-1]==tu)>0:
                    #     print timeslots
                    #     print 'debugahere'

                    if sum(sch[i] for i in sch if i[0] == v and v != i[1] and i[2] == b and i[-1] == tu) > 0:
                        fwdapp[v, b, tu] = 1
                    else:
                        fwdapp[v, b, tu] = 0

    def checkDuplex(sch, fwd, fwdapp):
        timeslots = set([t[-1] for t in sch])
        for tdup in timeslots:
            for v in node_set:
                if sum(sch[vi, v, b, tdup] for b in appPort_set for vi in node_set if
                       vi != v and (vi, v, b, tdup) in sch) >= 1 \
                        and fwd[v, tdup] == 1:
                    return False
                if sum(fwdapp[v, b, tdup] for b in appPort_set) > 1:
                    return False
                if sum(sch[vi, v, b, tdup] for b in appPort_set for vi in node_set if
                       vi != v and (vi, v, b, tdup) in sch) > 1:
                    return False
        return True

    def checkCapacity(apps, v, capacityNode):
        # we assume that all sources have the same req, therefore we take the
        # first app (with multiple allocation) and check the capacity
        if isinstance(apps,list):
            app = apps[0]
        else:
            app = apps
        ## TODO: need to check: capacityNode as dict or as panda (to be consistent)
        #print capacityNode[v],float(capacityNode[v])
        #print '**'
        #print app
        #print appPort_data.loc[app]['demand']#,float(appPort_data.loc[app]['demand'])
        #print '************'


        if float(capacityNode[v]) - float(appPort_data.loc[app]['demand'])>= 0:
            mapf[app, v] = 1
            capacityNode[v] = float(capacityNode[v]) - float(appPort_data.loc[app]['demand'])
            # print app,v
            # print capacityNode
            return True
        return False

    def checkSINR(sch, fwd, txpwr):
        timeslots = set([t[-1] for t in sch])
        pwrTemp = copy.copy(txpwr)
        for vs in node_set:
            for vr in node_set:
                if vr != vs:
                    for timeslot in timeslots:
                        interference = sum(
                            [txpwr[vcount] * fwd[(vcount, timeslot)] * arc_data.loc[(vcount, vr)]['Attenuation'] for
                             vcount in node_set if vcount != vs and vcount != vr])
                        interferencefullPwr = sum(
                            [fwd[(vcount, timeslot)] * arc_data.loc[(vcount, vr)]['Attenuation'] for vcount in node_set
                             if vcount != vs and vcount != vr])
                        estPwr = SINRth * (No + interferencefullPwr) / arc_data.loc[vs, vr]['Attenuation']
                        if powerControl:
                            if (txpwr[vs] == (1 + errMargin) or txpwr[vs] < estPwr) and estPwr < 1.01:
                                txpwr[vs] = estPwr
                        if fwd[(vs, timeslot)] * SINRth > txpwr[vs] * fwd[(vs, timeslot)] * arc_data.loc[vs, vr][
                            'Attenuation'] / (No + interference):
                            return False

        return True

    # Check SINR constraint and estiomate transmit power from the interference in a specific timeslot
    def checkSINR_v2(sNode, eNode, aT, timeslot, txpwr, fwd):
        if sNode == eNode:
            return True

        # if reversable:
        #     sch[sNode, eNode, aT, timeslot] =0
        # get all transmitting nodes at this timeslot
        txNodes = [x[0] for x in fwd if x[1] == timeslot and fwd[x] > 0 and x[0]!=sNode]
        if txNodes:
            possiblePwr = []
            for vs in txNodes:
                if vs != sNode:
                    for vr in node_set:
                        if vr != vs and vr != sNode:
                            interference = sum(
                                [txpwr[vcount] * fwd[(vcount, timeslot)] * arc_data.loc[(vcount, vr)]['Attenuation'] for
                                 vcount in txNodes
                                 if vcount != vs and vcount != vr])
                            # interferencefullPwr = sum(
                            #     [fwd[(vcount, timeslot)] * arc_data.loc[(vcount, vr)]['Attenuation'] for vcount in txNodes if
                            #      vcount != vs and vcount != vr])
                            est = (SINRth * txpwr[vs] - No - interference) / arc_data.loc[(sNode, vr)]['Attenuation']
                            possiblePwr.append(est)
            if possiblePwr:
                selectPwr = min(possiblePwr)
            else:
                selectPwr = 1
            if selectPwr > txpwr[sNode]:
                if selectPwr > (1 + errMargin):
                    selectPwr = 1
            new_interference = sum(
                [txpwr[vcount] * fwd[(vcount, timeslot)] * arc_data.loc[(vcount, vr)]['Attenuation'] for vcount in
                 txNodes
                 if vcount != sNode and vcount != eNode and vcount != vr])
            if selectPwr * arc_data.loc[(sNode, eNode)]['Attenuation'] / (new_interference + No) >= SINRth:
                return True
            return False
        else:
            return True

        # Check SINR constraint and estiomate transmit power from the interference in a specific timeslot
        def checkSINR_v3(sNode, eNode, aT, timeslot):
            if sNode == eNode:
                return True
            # if reversable:
            #     sch[sNode, eNode, aT, timeslot] =0
            # get all transmitting nodes at this timeslot
            txNodes = [x[0] for x in fwd if x[1] == timeslot and fwd[x] > 0]
            if txNodes:
                possiblePwr = []
                for vs in txNodes:
                    if vs != sNode:
                        for vr in node_set:
                            if vr != vs and vr != sNode:
                                interference = sum(
                                    [txpwr[vcount] * fwd[(vcount, timeslot)] * arc_data.loc[(vcount, vr)]['Attenuation']
                                     for
                                     vcount in txNodes if vcount != vs and vcount != vr])
                                # interferencefullPwr = sum(
                                #     [fwd[(vcount, timeslot)] * arc_data.loc[(vcount, vr)]['Attenuation'] for vcount in txNodes if
                                #      vcount != vs and vcount != vr])
                                est = (SINRth * txpwr[vs] - No - interference) / arc_data.loc[(sNode, vr)][
                                    'Attenuation']
                                possiblePwr.append(est)
                if possiblePwr:
                    selectPwr = min(possiblePwr)
                else:
                    selectPwr = 1
                if selectPwr > txpwr[sNode]:
                    if selectPwr > (1 + errMargin):
                        selectPwr = 1
                new_interference = sum(
                    [txpwr[vcount] * fwd[(vcount, timeslot)] * arc_data.loc[(vcount, vr)]['Attenuation'] for vcount in
                     txNodes if vcount != sNode and vcount != eNode])
                if selectPwr * arc_data.loc[(sNode, eNode)]['Attenuation'] / (new_interference + No) >= SINRth:
                    return True
                return False

        # pwrTemp = copy.copy(txpwr)
        # for vs in node_set:
        #     for vr in node_set:
        #         if vr!=vs:
        #             for timeslot in timeslots:
        #                 interference  = sum([txpwr[vcount]*fwd[(vcount,timeslot)]*arc_data.loc[(vcount,vr)]['Attenuation'] for vcount in node_set if vcount!=vs and vcount!=vr])
        #                 interferencefullPwr  = sum([fwd[(vcount,timeslot)]*arc_data.loc[(vcount,vr)]['Attenuation'] for vcount in node_set if vcount!=vs and vcount!=vr])
        #                 estPwr = SINRth*(No+interferencefullPwr)/arc_data.loc[vs,vr]['Attenuation']
        #                 if powerControl:
        #                     if (txpwr[vs]==(1+errMargin) or txpwr[vs]<estPwr) and estPwr<1.01:
        #                         txpwr[vs]=estPwr
        #                 if fwd[(vs,timeslot)]*SINRth > txpwr[vs]*fwd[(vs,timeslot)]*arc_data.loc[vs,vr]['Attenuation']/(No+interference):
        #                     return False
        #
        #
        # return True

    def isMapped(app, mapf):
        for v in node_set:
            if mapf[app, v] == 1:
                return True, v
        return False, None

    def addTimeSlot(sch, fwdapp):
        ### Graph
        oldSlots = list(set([i[-1] for i in sch]))
        newSlot = len(oldSlots)
        newSlots = oldSlots + [newSlot]
        for i in Graph.keys():
            oldValue = copy.copy(Graph[i])
            oldValue = oldValue + [[v, newSlot] for v in node_set if v != i[0]]
            Graph[(i, 0)] = oldValue

        for v in node_set:
            Graph[v, newSlot] = [[vv, slot] for slot in newSlots for vv in node_set if v != vv]

        ### s
        for v in node_set:
            for vv in node_set:
                for b in appPort_set:
                    sch[v, vv, b, newSlot] = 0

        ### fwdapp
        for v in node_set:
            for b in appPort_set:
                fwdapp[v, b, newSlot] = 0

    def checkSuccess(mapf):
        for app in apps_set:
            if sum(mapf[app, v] for v in node_set) != 1:
                return False
        return True

    # print find_first_path(graph, 'A', 'D')
    fpath = []
    for startApp in srcAppList:
        checkCapacity(startApp, srcNode, capacityNode)
    checkCapacity(endApp, endNode, capacityNode)
    start_time = time.time()
    # try:

    for link in chain_set:
        portDest = [l[1] for l in chain_set if l[0]==link[-1]]
        if portDest:
            portDest = portDest[0]

        isplaced, node = isMapped((link[-1]), mapf)
        srcflag, startnode = isMapped((link[0]), mapf)
        if isplaced:
            #print '****Already mapped*****', 'check ', (startnode, 0), node, '*********', (link[0], link[-1])
            #print 2,startnode
            fpath_r, scho = find_first_path(Graph, (startnode, 0), node, (link[0], link[1]), txpwro, scho, fwdo,
                                            fwdappo)
            fpath = fpath + fpath_r
            addToSch(fpath_r, scho, link[0])
            #print 'chosenAlready*****', fpath
            #print [i for i in scho if scho[i] == 1]

        else:
            for v in node_set:
                portDest = [l[1] for l in chain_set if l[0] == link[-1]][0]
                if checkCapacity((link[-1]), v, capacityNode):
                    #print '****to  map*****', 'check ', (startnode, 0), v, '*********', (link[0], link[-1])
                    #print 3,startnode
                    fpath_r, scho = find_first_path(Graph, (startnode, 0), v, (link[0], link[1]), txpwro, scho, fwdo,
                                                    fwdappo)
                    fpath = fpath + fpath_r
                    addToSch(fpath_r, scho, link[0])

                    #print 'chosenTomap*****', fpath
                    #print [i for i in scho if scho[i] == 1]

                    break
    # except Exception as  e:
    # print("Heuristic Failed")

    #    print sys.exc_info()[0]
    #    raise
    end_time = time.time() - start_time

    # print fpath
    # for j in appPort_set:
    #     print '*** path', j
    #     for i in sch:
    #         if sch[i]==1 and i[0]!=i[1] and i[2]==j:
    #             print i
    print '****************** Reults ******************'
    # print 'Capacity = ', capacityNode
    # print 'map= ', [i for i in map if map[i] == 1]
    #
    # def saveVar(varName, filename):
    #     with open('results/' + filename, "wb") as f:
    #         pickle.dump(varName, f)
    #
    # saveVar({'time': end_time,
    #          'number': len(set([t[-1] for t in scho])),
    #          's': [i for i in scho if scho[i] > 0.2],
    #          'power': [(i, txpwro[i]) for i in txpwro if txpwro[i] > 0],
    #          'f': [i for i in fwdo if fwdo[i] > 0.9], 'map': [i for i in map if map[i] > 0.9]},
    #         'HPower' + str(len(node_set)) + 'Topology' + str(topology) + 'Napps' + str(nr_apps) + 'Cap' + str(
    #             nodeCapacity) + str(trialx) + '.pickle')
    # checkSINR()
    # savedVar = {'time': end_time,
    #              'number':len(set([t[-1] for t in sch])),
    #              's':[i for i in sch if sch[i] >0.2],
    #              'power':[(i,txpwr[i]) for i in txpwr if txpwr[i] >0],
    #              'f':[i for i in fwd if fwd[i] > 0.9], 'map':[i for i in map if map[i] >0.9]}
    # print 'txPower ***************', txpwr
    # for  i in savedVar:
    #     print i,savedVar[i]
    # print checkSINR_v2()
    #if checkSuccess(mapf):
        #    print checkSINR_v2()

        #print 'required timeslots by Heurstic : ', len(set([t[-1] for tc in scho if scho[tc] == 1]))
        #print 'computation time by Heuristic: ', end_time
        #for i in txpwro:
        #    if txpwro[i] > 0:
        #        print "Tx power", i, txpwro[i]
        # print checkSINR()
        # print checkSuccess()

        # for i in map:
        #     if map[i] == 1:
        #         print i

    # print [i for i in sch if sch[i]==1]
    # print find_first_path(Graph, ['A',0], 'D',appT)
    # print checkDuplex()
    # print [i for i in map if map[i]==1]
#    s = {(b,i, j,  tt): 0 for i in node_set for j in node_set for b in list(appPort_set) for tt in t}
    s = {(c[2],c[0], c[1],  c[3]): scho[c] for c in scho}
    # s = {(b,i, j,  tt): scho[i,j,b,tt] for i in node_set for j in node_set for b in list(appPort_set) for tt in t}

    generate_xml(s, mapf, chain_set, srcAppList, sinkApp, sinkNode, dictParam, dictExec,givenPatha)

#optimizeAllocation()
#heuristicAllocation()
