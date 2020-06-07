import pandas as pd
import numpy as np
import string
import random
import itertools
import math
from multiGraphVNEPower_Updated import runMARVELO
import pickle
from itertools import combinations,permutations


from matplotlib import pyplot as plt


def node_gen(size=6, chars=string.ascii_uppercase):
    # generates random nodes with random IDs (e.g., A1 ,B2 , ...)
    numbers = range(80)
    domain = list(chars) + [''.join(map(str, e)) for e in list(itertools.product(chars, numbers))]
    return domain[:size]


def param_gen2(
        nr_nodes=5,
        nodename='node_sim.csv',
        nr_apps=4,
        seedIP=20, minNodeCapacity=21,
        maxNodeCapacity=22):
    np.random.seed(seedIP)
    nodes_id = node_gen(nr_nodes)
    df2 = pd.DataFrame(columns=['Node', 'capacity'])
    df2['Node'] = nodes_id
    df2['capacity'] = np.random.randint(minNodeCapacity, maxNodeCapacity, nr_nodes)
    # print df2['capacity']
    df2.to_csv(str(nodename))
    apps_id = range(1, nr_apps + 1)

    return nodes_id, apps_id


def arc_gen(nodes_id, arcname='arc0', scenario='random', seedIP=20, positionFile=None,dropLinks = [] ):
    np.random.seed(seedIP)
    if scenario == 'random':
        scaleAtten = 1
        Atten_val = scaleAtten * \
                    np.random.rand(len(nodes_id) * (len(nodes_id) - 1))

        # Atten_val = [ 0.89864337,  0.78994424,  0.25271711,  0.42760049,  0.83680771,\
        #    0.14214475,  0.69158715,  0.6403577 ,  0.73303505,  0.34868657,\
        #    0.19433637,  0.86121604,  0.42736361,  0.65452334,  0.54597408,\
        #    0.95871212,  0.49772796,  0.30672871,  0.75623525,  0.43760573]

        df = pd.DataFrame(
            columns=[
                'Start',
                'End',
                'Attenuation'])
        df['Attenuation'] = Atten_val
        df[['Start', 'End']] = np.array(list(itertools.permutations(nodes_id, 2)))
        df2 = pd.DataFrame(columns=['Start', 'End'])
        df2['Start'] = nodes_id
        df2['End'] = nodes_id
        df.to_csv(str(arcname))
    elif (scenario == 'uniform'):
        nodesPosition = generate_positions(nodes_id)
        if positionFile:
            dpos = pd.DataFrame(nodesPosition)
            dpos.to_csv(positionFile, sep=';')
        nxn = compute_attenuation(nodes_id, nodesPosition, gamma=-2,dropLinks=dropLinks)
        df = pd.Series(nxn).reset_index()
        df.columns = ['Start', 'End', 'Attenuation']
        df.to_csv(str(arcname))
        # if positionFile:

        print('#############\nUniform\n##########')

    elif (scenario == 'randomUniform'):
        nodesPosition = generateRandomUniformPositions(nodes_id, seedIP=seedIP)
        if positionFile:
            dpos = pd.DataFrame(nodesPosition)
            dpos.to_csv(positionFile, sep=';')
        nxn = compute_attenuation(nodes_id, nodesPosition, gamma=-2,dropLinks=dropLinks)
        df = pd.Series(nxn).reset_index()
        df.columns = ['Start', 'End', 'Attenuation']
        df.to_csv(str(arcname))
        print('#############\nRandomUniform\n##########')


def compute_attenuation(nodesid, n, gamma, dropLinks=[]):
    # nxn ={(i,j):0 for i in nodesid  for j in nodesid if i!=j}
    dist = lambda a, b: ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
    nxn = {(i, j): min(dist(n[i], n[j]) ** gamma,1) for i in nodesid for j in nodesid if i != j}
    if dropLinks:
        for i in dropLinks:
            nxn[i] =0
    return nxn


def generate_positions(nodesid):
    iv = num = len(nodesid) ** 0.5
    if iv == math.ceil(iv):
        xv = np.linspace(0, 25, num=len(nodesid) ** 0.5)
        yv = np.linspace(0, 25, num=len(nodesid) ** 0.5)
    else:
        xv = np.linspace(0, 25, num=len(nodesid) * 0.5)
        yv = np.linspace(0, 25, 2)
    nodes = np.array([nodesid]).reshape((len(xv), len(yv)))
    xx, yy = np.meshgrid(xv, yv)
    nodes = {nodes[i, j]: [xx[j, i], yy[j, i]] for i in range(0, len(xv)) for j in range(0, len(yv))}
    # plt.plot(xx, yy, marker='.', color='k', linestyle='none')
    # plt.show()
    return nodes


def generateRandomUniformPositions(nodesid, width=25, height=25, seedIP=20):
    np.random.seed(seedIP)
    xv = np.random.uniform(0, width, len(nodesid))
    yv = np.random.uniform(0, height, len(nodesid))

    nodes = {nodesid[i]: [xv[i], yv[i]] for i in range(len(nodesid))}
    # nodes = {nodes[i, j]: [xx[j, i], yy[j, i]] for i in range(0, len(xv)) for j in range(0, len(yv))}
    # plt.plot(xx, yy, marker='.', color='k', linestyle='none')
    # plt.show()
    return nodes


def generateLinearChain(nr_apps, seedip, chainFile='simParam/chain_Linear', appSim='simParam/appSim', capGen='random'):
    # Generates a linear overlay graph as well as the requirements of each task in the overlay graph
    # Overlay graph = chainFile
    #       srcTask, port, dstTaks
    # Requirements of each Task =  appSim
    #       Task , Requirement
    np.random.seed(seedip)
    df = pd.DataFrame(
        columns=[
            'srcapp',
            'srcport',
            'dstapp'])

    df['srcapp'] = np.arange(1, nr_apps)
    df['srcport'] = np.repeat(1, nr_apps - 1)
    df['dstapp'] = np.arange(2, nr_apps + 1)
    df.to_csv(str(chainFile))

    df2 = pd.DataFrame(
        columns=[
            'srcapp',
            'port',
            'demand'])
    nodes = np.arange(1, nr_apps + 1)
    df2['srcapp'] = nodes
    df2['port'] = np.repeat(1, len(nodes))
    if capGen == 'random':
        demand = 20 * np.random.rand(len(nodes))
    else:
        demand = np.repeat(20, (len(nodes)))

    demand[0] = 0
    demand[-1] = 0
    df2['demand'] = demand
    df2.to_csv(str(appSim))
    return nodes


def generateParallelChain(nr_apps, seedip, chainFile='simParam/chain_parallel', appSim='simParam/appSim',
                          capGen='random'):
    # Generates a parallel overlay graph as well as the requirements of each task in the overlay graph
    # Overlay graph = chainFile
    #       srcTask, port, dstTaks
    # Requirements of each Task =  appSim
    #       Task , Requirement
    np.random.seed(seedip)
    df = pd.DataFrame(
        columns=[
            'srcapp',
            'srcport',
            'dstapp'])
    src_1 = np.repeat(1, nr_apps - 2)
    src_2 = np.arange(2, nr_apps)
    dst_1 = np.repeat(nr_apps, len(src_2))
    src_t = np.concatenate((src_1, src_2), axis=0)
    df['srcapp'] = src_t
    df['srcport'] = np.repeat(1, len(src_t))
    df['dstapp'] = np.concatenate((src_2, dst_1), axis=0)
    df.to_csv(str(chainFile))

    df2 = pd.DataFrame(
        columns=[
            'srcapp',
            'port',
            'demand'])
    nodes = np.arange(1, nr_apps + 1)
    df2['srcapp'] = nodes
    df2['port'] = np.repeat(1, len(nodes))
    if capGen == 'random':
        demand = 20 * np.random.rand(len(nodes))
    else:
        demand = np.repeat(20, (len(nodes)))
    demand[0] = 0
    demand[-1] = 0
    df2['demand'] = demand
    df2.to_csv(str(appSim))





def loadVar(filename):
    return pickle.load(open(filename, "rb"))


def runSimulationSetup(nodesList, apssList, seedList, nodeCapacity, randomCapacity=False,flagToDrop=False):
    for nr_nodes in nodesList:  # range(4,10):# nr of nodes
        for nr_apps in apssList:  # range (3,7):# nr of tasks/blocks
            if nr_apps <= nr_nodes + 2:
                for seed in seedList:  # range(0,50): # seed for  reproducing random variables
                    # try:
                    #     loadPower = loadVar('results' + '/Power' + str(nr_nodes) + 'Topology' + str(topology) + 'Napps' + str(
                    #         nr_apps) + 'Cap' + str(nodeCapacity) + str(seed) + '.pickle')
                    # except:
                        print('nodes', nr_nodes, ' blocks', nr_apps, ' seed', seed)
                        nodesfile = "param/" + 'n' + str(nr_nodes) + str(seed) + '.csv'
                        arcsfile = "param/" + 'a' + str(nr_nodes) + str(seed) + '.csv'
                        chainsLinear = "param/" + 'chain_linear_' + str(nr_apps) + '.csv'
                        # chainsParallel = 'chain_parallel_'+str(nr_apps)
                        # Names of CSV files (path/name.csv)"
                        appSimFile = "param/" + 'b' + str(nr_apps) + str(seed) + '.csv'
                        positionsFile = "param/" + 'pos' + str(nr_nodes) + str(seed) + '.csv'

                        # Capacity of nodes:
                        #    can be fixed : e.g., nodeCapacity=21
                        #    or random : eg. minCap = 5, maxCap = 25
                        if randomCapacity:
                            maxNodeCapacityMax = nodeCapacity * (2 + abs(np.random.rand(1)[0]))
                        else:
                            maxNodeCapacityMax = nodeCapacity + 1

                        # Generate Infrastructure graph and give names/IDs for tasks/blocks/apps in the overlay graph
                        np.random.seed(seed=seed)
                        nodes_id, apps_id = param_gen2(nr_nodes=nr_nodes,
                                                       nodename=nodesfile,
                                                       nr_apps=nr_apps,
                                                       seedIP=seed,
                                                       minNodeCapacity=nodeCapacity,
                                                       # maxNodeCapacity=nodeCapacity * (2 + abs(np.random.rand(1)[0])))
                                                       maxNodeCapacity=maxNodeCapacityMax)

                        # Distribute and calculate the attenuation between the nodes

                        # Generate a random overlay topology. Either:
                        # Parallel
                        # generateParallelChain(len(apps_id),chainsParallel,appSimFile)
                        # or Linear
                        apps = generateLinearChain(len(apps_id), seed, chainsLinear, appSimFile, capGen='uniform')

                        # select random source and sink nodes
                        random.seed(seed)
                        dropLinks = []
                        if flagToDrop:
                            arcs = list(permutations(nodes_id, 2))
                            dropIndex = np.mod(seed, len(arcs))
                            dropLinks = [arcs[dropIndex], tuple(reversed(arcs[dropIndex]))]
                        if seed <len(nodes_id)**2:
                            sinkIndex = seed%len(nodes_id)
                            sinkNode = nodes_id[sinkIndex] #random.choice(nodes_id)
                            srcIndex = int(seed / len(nodes_id))
                            sourcenode = nodes_id[srcIndex]#random.choice(nodes_id)

                            arc_gen(nodes_id, arcname=arcsfile, scenario='uniform', positionFile=positionsFile,
                                    seedIP=seed,dropLinks=dropLinks)
                        else:
                             sinkNode = random.choice(nodes_id)
                             sourcenode = random.choice(nodes_id)
                             arc_gen(nodes_id, arcname=arcsfile, scenario='randomUniform', positionFile=positionsFile,
                                seedIP=seed,dropLinks=dropLinks)

                        sink = sinkNode
                        # print(srcIndex)

                # run marvelo
                        src = sourcenode
                        trialx = seed
                        chainsfile = chainsLinear
                        topology = 'linear'
                        SINRth = 20
                        print(src)
                        print(sink)
                        srcBlock = apps[0]
                        sinkBlock = apps[-1]
                        try:
                            # execfile('multiGraphVNEPower.py')
                            # print(apps)
                            # print(nodes_id)
                            code_block = compile(open('multiGraphVNEPower_Updated.py').read(),
                                                 'multiGraphVNEPower_Updated.py',
                                                 'exec')
                            blob = {}
                            exec(code_block, blob)
                            runMARVELO(sourcenode, sinkNode, srcBlock, sinkBlock, chainsfile, appSimFile, arcsfile,
                                       nodesfile,
                                       SINRth, topology, nodeCapacity, seed)
                            # exec(open('multiGraphVNEPower_Updated.py').read())
                            # import  multiGraphVNEPower_Updated
                        except Exception as e:
                            print(str(e))


#### Example on generation
nodesList = [4] #range(4, 12)  # [4]
apssList = [3] #range(3, 10)  # [4]
seedList =[11]#[2024]# range(10000,20000)#range(nodesList[0]**2)#range(50)  # [3]
nodeCapacity = 21
randomCapacity = False
dropLinksFlag=False
runSimulationSetup(nodesList, apssList, seedList, nodeCapacity, randomCapacity=False,flagToDrop=dropLinksFlag)
# dropLinksFlag = True
# seedList = range(1)
# runSimulationSetup(nodesList, apssList, seedList, nodeCapacity, randomCapacity=False,flagToDrop=dropLinksFlag)
