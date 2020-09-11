from pyomo.environ import *
import pyomo.environ
import math
# import pyomo
import pandas
import logging
import time
import pickle
def runMARVELO(src,sinkNode,srcBlock,sinkBlock,chainsfile,appSimFile,arcsfile,nodesfile,SINRth,topology,nodeCapacity, seed):


    # nodesfile ="substrate_nodes.csv"# 'n'+str(nr_nodes)+str(seed)+'.csv'
    # arcsfile = "substrate_links.csv"# 'a' + str(nr_nodes) +str(seed)+ '.csv'
    # chainsLinear = "overlay_links.csv"#'chain_linear_'+str(nr_apps)+ '.csv'
    # # chainsParallel = 'chain_parallel_'+str(nr_apps)
    # appSimFile = "overlay_blocks.csv"#'b'+str(nr_apps) +str(seed)+'.csv'
    #
    # sinkNode = 3#'SINK'# random.choice(nodes_id)
    # sink = sinkNode
    # sourcenode = 0##random.choice(nodes_id)
    #
    # sinkBlock = 'SINK'
    # srcBlock =  'SOURCE'
    # #run marvelo
    # src = sourcenode
    # trialx = 1
    # chainsfile = chainsLinear
    # topology = 'linear'
    # SINRth= 20



    model = ConcreteModel()
    # src ='D'
    # sinkNode='A'
    # trialx=0
    # srcNode=src
    # nr_apps=4
    # nr_nodes = 6
    # topology = 'parallel'
    #
    # SINRth=67


    ##
    ''' Directories with concrete values'''
    # node
    # nodesfile = 'simParam/nodeSim_' + str(trialx) + '.csv'
    # nodesfile = 'simParam/nodeSim_N' + str(trialx) + '.csv'
    # # component
    # appsfile = 'simParam/sim_' + str(trialx) + '.csv'
    # # appSim
    # appSimFile = 'simParam/appsim_1'+'.csv'
    # # edges
    # arcsfile = 'simParam/arcs_' + str(trialx) + '.csv'
    # # vnf
    # chainsfile = 'simParam/chain_' + str(1) + '.csv'



    # appsfile = 'simParam/sim_N'+str(nr_nodes)+'.csv'
    # nodesfile = 'simParam/nodeSim_N'+str(nr_nodes)+'.csv'
    # arcsfile = 'simParam/arcs_N' + str(nr_nodes) + '.csv'
    # appSimFile = 'simParam/appsim_'+str(nr_apps)+'.csv'
    # if topology == 'parallel':
    #     chainsfile = 'simParam/chain_parallel_'+str(nr_apps)
    # elif topology == 'linear':
    #     chainsfile = 'simParam/chain_linear_'+str(nr_apps)


    '''load concrete parameters'''
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
    # edge index
    arc_set = list(arc_data.index.unique())
    # appPort index
    appPort_set = appPort_data.index.unique()
    # chain index
    chain_set = chain_data.index.unique()
    chain_set = sorted(chain_set, key=lambda tup: tup[1])
    # chain_set = [(1,2),(2,3),(3,2),(3,4)]
    # component inex
    apps_set = set(appsfile_data.index.unique())
    nr_apps = len(list(apps_set))
    nodeCapacity = nodeCapacity
    trialx = seed

    '''Other concrete paramaeters'''
    ## predefined mapping: {(1, 'A'), (5, 'E')} {src,dest}, of course can be extended to mulitple source (with component '1')
    #mapping_set = {(list(apps_set)[0], list(node_set)[0]), (list(apps_set)[-1], list(node_set)[-1])}
    # mapping_set = {(list(apps_set)[0],src), (list(apps_set)[-1], sinkNode)}
    mapping_set = {(srcBlock,src), (sinkBlock, sinkNode)}
    print(mapping_set)
    # sinkNode = list(node_set)[-1]
    sinkApp = list(apps_set)[-1]
    srcApp = list(apps_set)[0]
    maxTimeslots = 6
    timeslots_set = range(1, maxTimeslots + 1)
    timeBound = 3
    #timeslots_set = range(3, maxTimeslots + 1)
    bigM = 1e3
    #SINRth = 2
    #model.SINRth = 1.5
    model.noise = 0.000019

    ''' Intializing model sets'''
    model.nodes = Set(initialize=node_set)
    model.components = Set(initialize=apps_set)
    #multi-index is not supported in new Pyomo versions
    #https://github.com/Pyomo/pyomo/issues/1564
    # model.appPorts = Set( initialize=appPort_set, dimen=2)
    model.appPorts = Set( initialize=list(appPort_set.values), dimen=2)
    model.timeslots = Set(initialize=timeslots_set)
    model.vnf = Set(initialize=chain_set, dimen=3)
    model.edges = Set(initialize=arc_set, dimen=2)
    model.mapping = Set(initialize=mapping_set, dimen=2)

    ''''Variables'''
    model.usedTimeslots = Var(model.timeslots, within=Boolean)
    model.map = Var(model.appPorts * model.nodes, within=Boolean)
    model.fwdNode = Var(model.appPorts*model.nodes*model.timeslots, within = Boolean)
    model.schedule = Var(model.appPorts*model.nodes*model.nodes * model.timeslots, domain=Boolean)
    # model.powertx = Var(model.nodes*model.nodes* model.timeslots, domain=NonNegativeReals, bounds=(0, 1))
    model.powertx = Var(model.nodes*model.nodes* model.timeslots, domain=Boolean)
    model.h = Var(model.appPorts*model.nodes*model.nodes,domain= NonNegativeIntegers)
    model.z =Var(model.edges*model.timeslots,domain= NonNegativeReals)


    # Create an IMPORT Suffix to store the iis information that will
    # be returned by gurobi_ampl
    # model.iis = Suffix(direction=Suffix.IMPORT)

    #### Intialize values ######
    for i in model.h:
            model.h[i].value=0
    # #
    for i in model.schedule:
        model.schedule[i].value = 0

    for i in model.map:
        model.map[i].value = 0

    ############################################################
    # Constraints
    ############################################################

    ## relating power to transmission s
    # def upperPower(model,node1,timeslot):
    #    return model.powertx[node1,timeslot]<= sum([model.fwdNode[c,node1,timeslot] for c in model.appPorts])
    # model.upperPower = Constraint(model.nodes,model.timeslots,rule =upperPower)
    #
    # def lowerPower(model,node1,timeslot):
    #    return bigM*model.powertx[node1,timeslot]>= sum([model.fwdNode[c,node1,timeslot] for c in model.appPorts])
    # model.lowerPower = Constraint(model.nodes,model.timeslots,rule =lowerPower)

    ## relating power to transmission s
    def upperPower(model, node1, node2, timeslot):
        if node1 != node2:
            pass
        return model.powertx[node1, node2, timeslot] <= sum(
            [model.schedule[c, node1, node2, timeslot] for c in model.appPorts])
        return Constraint.Skip

    model.upperPower = Constraint(model.nodes, model.nodes, model.timeslots, rule=upperPower)

    def lowerPower(model, node1, node2, timeslot):
        if node1 != node2:
            return bigM * model.powertx[node1, node2, timeslot] >= sum(
                [model.schedule[c, node1, node2, timeslot] for c in model.appPorts])
        return Constraint.Skip

    model.lowerPower = Constraint(model.nodes, model.nodes, model.timeslots, rule=lowerPower)

    ## relaxation using z
    ######################
    # def sandZlowLimit(model,node1,node2,timeslot):
    #     return model.z[node1,node2,timeslot] >=0
    # model.sandZlowLimit = Constraint(model.edges,model.timeslots,rule =sandZlowLimit)
    #
    # def sandZupLimit(model, node1,node2,timeslot):
    #     edgeActive = sum([model.schedule[a, node1,node2, timeslot] for a in model.appPorts])
    #     return model.z[node1,node2,timeslot] <=edgeActive*(len(model.appPorts)*len(model.nodes)-1)
    # model.sandZupLimit = Constraint(model.edges,model.timeslots,rule=sandZupLimit)
    #
    # def sandFlowLimit(model,node1,node2,timeslot):
    #     edgeActive = sum([model.schedule[a, node1,node2, timeslot] for a in model.appPorts])
    #     interference = sum(sum(
    #         model.fwdNode[c, v, timeslot] * arc_data.ix[(v, node2), 'Attenuation']for
    #         v in model.nodes if v != node1 and v != node2)
    #                        for c in model.appPorts)
    #     return model.z[node1,node2,timeslot] >= interference - (len(model.appPorts)*len(model.nodes)-1)*(1-edgeActive)
    # model.sandFlowLimit = Constraint(model.edges,model.timeslots,rule=sandFlowLimit)
    #
    # def sandFupLimit(model,node1,node2,timeslot):
    #     interference = sum(sum(
    #         model.fwdNode[c, v, timeslot]* arc_data.ix[(v, node2), 'Attenuation']
    #                    for v in model.nodes if v != node1 and v != node2)
    #                        for c in model.appPorts)
    #     return model.z[node1,node2,timeslot]<=interference
    # model.sandFupLimit = Constraint(model.edges,model.timeslots,rule=sandFupLimit)
    def sandZlowLimit(model, node1, node2, timeslot):
        return model.z[node1, node2, timeslot] >= 0

    model.sandZlowLimit = Constraint(model.edges, model.timeslots, rule=sandZlowLimit)

    def sandZupLimit(model, node1, node2, timeslot):
        edgeActive = sum([model.schedule[a, node1, node2, timeslot] for a in model.appPorts])
        return model.z[node1, node2, timeslot] <= edgeActive * (len(model.appPorts) * len(model.nodes) - 1)

    model.sandZupLimit = Constraint(model.edges, model.timeslots, rule=sandZupLimit)

    def sandFlowLimit(model, node1, node2, timeslot):
        edgeActive = sum([model.schedule[a, node1, node2, timeslot] for a in model.appPorts])
        interference = sum(
            model.powertx[v, v2, timeslot] * arc_data.loc[(v, node2), 'Attenuation'] for
            v, v2 in model.edges if v != node1 and v != node2)

        return model.z[node1, node2, timeslot] >= interference - (len(model.appPorts) * len(model.nodes) - 1) * (
                    1 - edgeActive)

    model.sandFlowLimit = Constraint(model.edges, model.timeslots, rule=sandFlowLimit)

    def sandFupLimit(model, node1, node2, timeslot):
        interference = sum(
            model.powertx[v, v2, timeslot] * arc_data.loc[(v, node2), 'Attenuation']
            for v, v2 in model.edges if v != node1 and v != node2)

        return model.z[node1, node2, timeslot] <= interference

    model.sandFupLimit = Constraint(model.edges, model.timeslots, rule=sandFupLimit)

    ## limiting h
    def limitH(model,node1,node2,component,port):
        succ_p = list(filter(lambda x: (x[0] == component and x[1] == port), model.vnf))
        if succ_p:
            return model.h[component,port, node1,node2]<=len(succ_p)
        return Constraint.Skip
    model.limitH = Constraint(model.nodes,model.nodes,model.appPorts,rule=limitH)


    ##Placement Constraints
    ############################################################
    ''' every component needs to be mapped only once to a node
     special treatment for compnents that have predefined mappings'''


    def componentIsMapped(model, component,portNr):
        premapped = list(filter(lambda x: x[0] == component, model.mapping))
        if premapped:
            # print premapped
             #print component, portNr, premapped[0][1]
             model.map[component,portNr, premapped[0][1]] = 1
             model.map[component, portNr,premapped[0][1]].fixed = True
        return sum([model.map[component,portNr, n] for n in model.nodes]) == 1

    model.componentIsMapped = Constraint(model.appPorts, rule=componentIsMapped)


    '''A node is not overutilized by the number of running instances '''

    # def capacityConstraintConcrete(model, node):
    #     return sum(model.map[c, node] * list(appsfile_data.ix[c]['demand'])[0] for c in model.components) <= node_data.ix[
    #         node, 'capacity']
    def capacityConstraintConcrete(model, node):
        return sum(model.map[c, node] * appPort_data.loc[c]['demand'] for c in model.appPorts) <= node_data.loc[
            node, 'capacity']
    model.capacityConstraint = Constraint(model.nodes, rule=capacityConstraintConcrete,name="capacity")

    # # every component needs to be mapped to at MOST one  node
    def componentMappedAtMostOnce(model, component,port):
        return sum([model.map[component,port, n] for n in model.nodes]) == 1
    model.componentMappedAtMostOnce = Constraint(model.appPorts, rule=componentMappedAtMostOnce)

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

    def mapDontReceive(model, component,port,node):
        incomingedges = list(filter(lambda x: x[1] == node, model.edges))

        return model.map[component,port, node] + sum([model.h[component,port, e] for e in incomingedges if e[0]!=node]) <= 1
    model.mapDontReceive = Constraint(model.appPorts,model.nodes, rule=mapDontReceive)

    # Forwarding constraints
    ############################################################


    ''' A node must send a vnf, only if it received the previous instance(s) in the chain or received the vnf '''
    def flowControl(model,component,port,node):
        if component == srcApp and node == src:
                succ_p = list(filter(lambda x: (x[0] == component and x[1]==port), model.vnf))
                outgoing = list(filter(lambda x: x[0] == node, model.edges))
                outgoing.append((node,node))
                return sum(model.h[component,port,e] for e in outgoing )-model.map[component,port,node]*len(succ_p)==0

        elif component == sinkApp and node == sinkNode:
                preds_p =list(filter(lambda x: x[2] == component, model.vnf))
                incoming = list(filter(lambda x: x[1] == node, model.edges))
                incoming.append((node, node))

                return sum(model.h[c[0],c[1],e] for c in preds_p for e in incoming )-model.map[component,port,node]*len(preds_p)>=0 # for loop placement
        else:
            succ_p = list(filter(lambda x: (x[0] == component and x[1]==port), model.vnf))
            preds_p = list(filter(lambda x: x[2] == component, model.vnf))
            outgoing = list(filter(lambda x: x[0] == node, model.edges))
            outgoing.append((node, node))

            incoming = list(filter(lambda x: x[1] == node, model.edges))
            incoming.append((node, node))

            return sum(model.h[component,port,e] for e in outgoing )-model.map[component,port,node]*len(succ_p) == sum(model.h[component,port,e] for e in incoming )-sum(model.map[c[2],1,node]  for c in succ_p)
    model.flowControl = Constraint(model.appPorts, model.nodes, rule=flowControl)

    # A node may send the traffic to itself and then to the others without actually running the block or receiving it
    # from other node
    def preventSelfLoop(model,component,port,node):
        preds_p = list(filter(lambda x: (x[2] == component and x[1] == port), model.vnf))
        incoming = list(filter(lambda x: x[1] == node, model.edges))
        succ_p = list(filter(lambda x: (x[0] == component and x[1] == port), model.vnf))

        if len(preds_p)>0 :
            # return model.h[component,port,node,node]*len(preds_p) <= sum(model.h[component,port,e] for e in
            # incoming)*len(preds_p)+ model.map[component,port,node]*len(succ_p)#sum(model.h[c[0],c[1],e] for e in
            # incoming for c in preds_p)
            return model.h[component,port,node,node] <= sum(model.h[component,port,e] for e in incoming)*len(preds_p)+ model.map[component,port,node]*len(succ_p)#sum(model.h[c[0],c[1],e] for e in incoming for c in preds_p)

        return Constraint.Skip
    model.preventSelfLoop = Constraint(model.appPorts, model.nodes, rule=preventSelfLoop,name="preventSelfLoop")

    # def mapAndH(model,component,port,node):
    #     # doesnot work for forwading node
    #     if component!= sinkApp:
    #         succ_p = filter(lambda x: (x[0] == component and x[1]==port), model.vnf)
    #         outgoing = filter(lambda x: x[0] == node, model.edges)
    #         outgoing.append((node, node))
    #         return bigM*model.map[component,port,node]*len(succ_p) - sum(model.h[component,port,e] for e in outgoing) >= 0
    #     return Constraint.Skip
    # model.mapAndH = Constraint(model.appPorts, model.nodes, rule=mapAndH)

    '''for every timeslot and every active, we need to check SINR constraint'''

    #update
    def SINR(model, source, destination, timeslot):
        edge = (source, destination)

        edgeActive = sum([model.schedule[ a,edge, timeslot]  for a in model.appPorts])

        # do serious checking:


        signal = arc_data.loc[(source, destination), 'Attenuation']

        #compute interference:
        interference =sum(
            model.powertx[v, timeslot] * arc_data.loc[(v, destination), 'Attenuation'] for
            v in model.nodes if v != source and v != destination)
        # interference = sum(sum(
        #     model.fwdNode[c, v, timeslot] * arc_data.ix[(v, destination), 'Attenuation'] for
        #     v in model.nodes if v != source and v != destination)
        #                    for c in model.appPorts)

        return edgeActive * model.powertx[source,timeslot]* signal >= edgeActive * (interference + model.noise)*SINRth
        # return edgeActive * signal >= edgeActive * (interference + model.noise)*SINRth

    def SINR(model, source, destination, timeslot):
        edge = (source, destination)
        edgeActive = model.powertx[source, destination, timeslot]
        signal = arc_data.loc[(source, destination), 'Attenuation']

        # compute interference:
        interference = sum(
            model.powertx[v, v2, timeslot] * arc_data.loc[(v, destination), 'Attenuation'] for
            v, v2 in model.edges if v != source and v != destination)
        # interference = sum(sum(
        #     model.fwdNode[c, v, timeslot] * arc_data.loc[(v, destination), 'Attenuation'] for
        #     v in model.nodes if v != source and v != destination)
        #                    for c in model.appPorts)

        # return edgeActive * model.powertx[source,timeslot]* signal >= edgeActive * (interference + model.noise)*SINRth
        return edgeActive * signal >= ((model.z[edge, timeslot] + edgeActive * model.noise) * SINRth)
        # return edgeActive * signal >= edgeActive * (interference + model.noise)*SINRth

    model.SINR = Constraint(model.edges, model.timeslots, rule=SINR)




    def printSINR(model, source, destination, timeslot):
        edge = (source, destination)
        edgeActive = sum([model.schedule[ a,edge, timeslot].value  for a in model.appPorts])
        signal = arc_data.loc[(source, destination), 'Attenuation']
        interference = sum(sum(
            model.fwdNode[c, v, timeslot].value * arc_data.loc[(v, destination), 'Attenuation'] for
            v in model.nodes if v != source and v != destination)
                           for c in model.appPorts)
        print (edgeActive * signal /  (interference +edgeActive*model.noise))
    # Variable dependency
    ############################################################
    '''define the relationship between schedule and map'''

    '''Map is checking if it receives the required vnf in the chain'''


    #
    # def fwdNodeUp (model,node,component,port,timeslot):
    #     outgoingedges = list(filter(lambda x: x[0] == node, model.edges))
    #     #outgoingedges.append((node, node))
    #     return model.fwdNode[component,port,node,timeslot] - sum(model.schedule[component,port,e,timeslot] for e in outgoingedges )<=0
    #
    # model.fwdNodeUp = Constraint(model.nodes, model.appPorts, model.timeslots, rule=fwdNodeUp)
    #
    #
    # def fwdNodeDown (model,node,component,port,timeslot):
    #     outgoingedges = list(filter(lambda x: x[0] == node, model.edges))
    #     #outgoingedges.append((node, node))
    #     return bigM*model.fwdNode[component,port,node,timeslot] - sum(model.schedule[component,port,e,timeslot] for e in outgoingedges )>=0
    #
    # model.fwdNodeDown = Constraint(model.nodes, model.appPorts, model.timeslots, rule=fwdNodeDown)
    #
    #
    # def SandHup(model,component,port,node1,node2):
    #     return model.h[component,port,node1,node2] - sum(model.schedule[component,port,node1,node2,t] for t in model.timeslots) >=0
    # model.SandHup = Constraint( model.appPorts,model.nodes,model.nodes, rule=SandHup)
    #
    #
    # def SandHdown(model,component,port,node1,node2):
    #     return model.h[component,port,node1,node2] - bigM*sum(model.schedule[component,port,node1,node2,t] for t in model.timeslots) <=0
    # model.SandHdown = Constraint( model.appPorts,model.nodes,model.nodes, rule=SandHdown)

    '''Map is checking if it receives the required vnf in the chain'''

    def fwdNodeUp(model, node, component, port, timeslot):
        outgoingedges = filter(lambda x: x[0] == node, model.edges)
        # outgoingedges.append((node, node))
        return model.fwdNode[component, port, node, timeslot] - sum(
            model.schedule[component, port, e, timeslot] for e in outgoingedges) <= 0

    model.fwdNodeUp = Constraint(model.nodes, model.appPorts, model.timeslots, rule=fwdNodeUp)

    def fwdNodeDown(model, node, component, port, timeslot):
        outgoingedges = filter(lambda x: x[0] == node, model.edges)
        # outgoingedges.append((node, node))
        return bigM * model.fwdNode[component, port, node, timeslot] - sum(
            model.schedule[component, port, e, timeslot] for e in outgoingedges) >= 0

    model.fwdNodeDown = Constraint(model.nodes, model.appPorts, model.timeslots, rule=fwdNodeDown)

    def SandHup(model, component, port, node1, node2):
        return model.h[component, port, node1, node2] - sum(
            model.schedule[component, port, node1, node2, t] for t in model.timeslots) >= 0

    model.SandHup = Constraint(model.appPorts, model.nodes, model.nodes, rule=SandHup)

    def SandHdown(model, component, port, node1, node2):
        return model.h[component, port, node1, node2] - bigM * sum(
            model.schedule[component, port, node1, node2, t] for t in model.timeslots) <= 0

    model.SandHdown = Constraint(model.appPorts, model.nodes, model.nodes, rule=SandHdown)

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
    def     solve(m):
        """Solve the model."""
        solver = pyomo.opt.SolverFactory('gurobi')
        # solver = pyomo.opt.SolverFactory('glpk')
        # solver = pyomo.opt.SolverFactory('gurobi_ampl')
        # solver.options['outlev'] = 1# tell gurobi to be verbose with output
        # solver.options['iisfind'] = 1 # tell gurobi to find an iis table for the infeasible model

        # start_time2 = time.clock()
        solver.options['ResultFile'] = "test.ilp"
        # solver.options['SolutionLimit'] = 100
        results = solver.solve(m, tee=False, keepfiles=False,)
        # print("solver status = ",results)
        # endTimeOpt2= (time.clock()-start_time2)
        if (results.solver.status != pyomo.opt.SolverStatus.ok):
            logging.warning('Check solver not ok?')
        if (results.solver.termination_condition != pyomo.opt.TerminationCondition.optimal):
            logging.warning('Check solver optimality?')
        #return results

    #
    # ############################################################
    # # Only dbugging
    # ############################################################


    def calcBER(s,f):
        p_noError =1
        #print 's',s
        uTS = [set([i[-1] for i in s if s[2]!=s[3]])]
        ss = [i for i in s if i[3]!=i[2]]
        for sig in ss:
            print (sig)
            interference = sum(
                arc_data.loc[(fwd[0], fwd[1]), 'Attenuation']
                for fwd in f if fwd[-1]==sig[-1] and fwd[1] == sig[3] and fwd[0] != sig[2] and fwd[0] != sig[3])
            s_to_n  = arc_data.loc[(sig[2], sig[3]), 'Attenuation']/(interference+0.000019)
            print ('snr = ',s_to_n)
            ser = math.erfc(s_to_n**0.5 * math.sin(3.14/32))
            p_SymbError = 1- p_noError*(1-ser)
        return p_SymbError

    def saveVar(varName,filename):
        with open(''+filename,"wb") as f:
            pickle.dump( varName, f)

    def loadVar(filename):
            return pickle.load(open('results/'+filename, "rb"))
    start_time_model = time.time()
    timeElapsed = solve(model)
    timeElapsed = time.time() - start_time_model
    # srcNode= [i for i in model.mapping][0][1]
    try:
        print ('\nnumber of opt used time slots= ', sum(model.usedTimeslots[i].value for i in model.timeslots))
        print ('mapping follows (component node): \n', [i for i in model.map if model.map[i] == 1], '\n')
        print ('Active Edges (src,dst,blcokToSend,timeslot) are:\n', set([(i[2:4],i[0],i[-1]) for i in model.schedule if model.schedule[i] == 1 and i[2]!=i[3]]), '\n')
        #print 'Scheduler follows \n', [i for i in model.schedule if model.schedule[i] == 1 if i[2] != i[3]]
        #print 'All paths within Scheduler follows \n', [i for i in model.schedule if model.schedule[i] == 1]
        #print 'saving file name: ' + str(len(node_set)) + str(trialx)
        print ('Elapsed time for the optimization model: ', timeElapsed)
        # print('src, sink = ', src,sinkNode)


        # for i in model.schedule:
        #     if model.schedule[i].value ==1 and i[2]!=i[3]:
        #         printSINR(model, i[2], i[3], i[-1])
        # print calcBER([i for i in model.schedule if model.schedule[i].value > 0.9],
        #                 [i for i in model.fwdNode if model.fwdNode[i].value > 0.9])
        #
        # for i in model.schedule:
        #     if model.schedule[i].value > 0.1 and i[-3]!=i[-2]:
        #         print 'schedule', i , model.schedule[i].value
        #
        # for i in model.h:
        #     if model.h[i].value > 0.1 and i[-1]!=i[-2]:
        #         print 'h', i , model.h[i].value
        # for i in model.powertx:
        #     if model.powertx[i].value >0.1:
        #         print 'power', i,  model.powertx[i].value
        #
        # for i in model.map:
        #     if model.map[i]==1:
        #         print "model.map[", i, "].value =1"
        #         print "model.map[", i, "].fixed =1"
        #
        # for i in model.schedule:
        #     if model.schedule[i]==1:
        #         print "model.schedule[", i, "].value =1"
        #         print "model.schedule[", i, "].fixed =1"
        # print 'Saving file: ','OptSource' + str(len(node_set))+'SINR'+str(SINRth) + 'T'+ str(trialx)
        # print 'Saving file: ','Power' + str(len(node_set)) + 'Topology' + str(topology) + 'Napps' + str(nr_apps)+'Cap'+str(nodeCapacity) +'Trial'+str(trialx)+ '.pickle'
        saveVar({'time': timeElapsed,
                 'number':sum(model.usedTimeslots[i].value for i in model.timeslots),
                 's':[i for i in model.schedule if model.schedule[i].value >0.2],
                 # 'power':[(i,model.powertx[i].value) for i in model.powertx if model.powertx[i].value >0.001],
                 'f':[i for i in model.fwdNode if model.fwdNode[i].value > 0.9], 'map':[i for i in model.map if model.map[i].value >0.9],
                 'srcNode':src,
                 'sinkNode':sinkNode}, 'results/Power' + str(len(node_set)) +'Topology'+str(topology) + 'Napps'+ str(nr_apps)+'Cap'+str(nodeCapacity)+ str(trialx)+ '.pickle')



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
    except Exception as e :
    #    saveVar({'time': timeElapsed, 'number': 'failed'}, 'OptSource' + str(src) + str(len(node_set)) + str(trialx)+ '.pickle')
    #    print 'Failed to find solution for napss',nr_apps, 'nodes',nr_nodes, 'Cap',str(nodeCapacity)
        print (e)

    def mapAndHTest(model,component,port,node):
        if component!= sinkApp:
            succ_p = list(filter(lambda x: (x[0] == component and x[1]==port), model.vnf))
            outgoing =list( filter(lambda x: x[0] == node, model.edges))
            outgoing.append((node, node))
            return bigM*model.map[component,port,node].value*len(succ_p) - sum(model.h[component,port,e].value for e in outgoing) >= 0
        return 'not my buisness'


    def limitHtest(model,node1,node2,component,port):
        succ_p = list(filter(lambda x: (x[0] == component and x[1] == port), model.vnf))
        if succ_p:
            print (model.h[component,port, node1,node2]<=len(succ_p))
    # model.limitH = Constraint(model.edges,model.appPorts,rule=limitH)

    def preventSelfLoopTest(model,component,port,node):
        preds_p = list(filter(lambda x: (x[2] == component and x[1] == port), model.vnf))
        incoming =list( filter(lambda x: x[1] == node, model.edges))
        succ_p = list(filter(lambda x: (x[0] == component and x[1] == port), model.vnf))

        if len(preds_p)>0:
            if not model.h[component,port,node,node].value <= sum(model.h[component,port,e].value for e in incoming)*len(preds_p)+ model.map[component,port,node].value*len(succ_p):#sum(model.h[c[0],c[1],e].value for e in incoming for c in preds_p):
                print (component,port,node)
                print (model.h[component,port,node,node].value*len(preds_p))
                print  (sum(model.h[component,port,e].value for e in incoming)*len(preds_p))
                print (sum(model.h[c[0],c[1],e].value for e in incoming for c in preds_p))

    def mapDontReceiveTest(model, component,port,node):
        incomingedges = list(filter(lambda x: x[1] == node, model.edges))
        for e in incomingedges:
            if model.map[component,port, node].value + sum([model.h[component,port, e].value for e in incomingedges if e[0]!=node]) > 1:
                print (component,port,node)

    def sandFlowLimitTest(model, node1, node2, timeslot):
        edgeActive = sum([model.schedule[a, node1, node2, timeslot].value for a in model.appPorts])
        interference = sum(
            model.powertx[v, v2, timeslot].value * arc_data.loc[(v, node2), 'Attenuation'] for
            v, v2 in model.edges if v != node1 and v != node2)

        if not model.z[node1, node2, timeslot].value >= interference - (len(model.appPorts) * len(model.nodes) - 1) * (
                    1 - edgeActive):
            print("value of z \n{}\n\n"
                  "value of RHS \n{}\n\n".format(
                model.z[node1, node2, timeslot].value,
                interference - (len(model.appPorts) * len(model.nodes) - 1) * (1 - edgeActive)
            ))
    for node1,node2 in model.edges:
        # for node2 in model.nodes:
            for timeslot in model.timeslots:
                sandFlowLimitTest(model, node1, node2, timeslot)
