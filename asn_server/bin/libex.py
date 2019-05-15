import lxml.etree as ET
from HTMLParser import HTMLParser
import os
h = HTMLParser()

## Topology
# vnf  =[(1,10,2),(2,20,3),(2,20,4),(3,30,5),(4,40,5)]
# # vnf_noPorts = [i[::2] for i in vnf]
# algs = list(sum(vnf, ()))
# nodes = {'A','B','C','D'}
# # ## palcement
# # srcNode = 'A'
# sinkNode = 'D'
# srcApp = 1
# sinkApp =5
# theta = {(i,j):0 for i in nodes for j in algs}
# theta[('A',1)] =1
# theta[('A',2)] =1
# theta[('B',3)] =1
# theta[('C',4)] =1
# theta[('D',5)] =1
# # ## routing
# s={}
# s[1,10,'A','A']=1
# s[2,20,'A','B']=1
# s[2,20,'A','C']=1
# s[3,30,'B','D']=1
# s[4,40,'C','D']=1

def getSendingNode(dst,alg,s):
    # find sending node to current dst,which requires alg
    sendingNodes= []
    #s = [i for i in si if si[i].value>0.9]
    for i in s:
        if i[3]==dst and i[0] == alg:
            sendingNodes.append(i[2])
    #sendingNodes=filter(lambda x,y,z: x[1]==dst and x[2] == alg,s)
    return sendingNodes

def getSendingNodeHeuristic(dst,alg,s):
    # find sending node to current dst,which requires alg
    sendingNodes= []
    #s = [i for i in si if si[i].value>0.9]
    for i in s:
        if i[2]==dst and i[0][0] == alg:
            sendingNodes.append(i[1])
    #sendingNodes=filter(lambda x,y,z: x[1]==dst and x[2] == alg,s)
    return sendingNodes

def getPrevAlg(alg,vnf):
    prevAlg = []
    for i in vnf:
        if i[2]==alg:
            prevAlg.append((i[0],i[1]))
    return prevAlg





## Build xml
def generate_xml(si,theta,vnf,srcApp,sinkApp,sinkNode,dictParam,dictExec,givenPath="put_your_path_here",allocMEthod = 'heuristic'):
    #remove timeslot param
      if allocMEthod == 'heuristic':
          s = set([i[:-1] for i in si if si[i] >0.9])
      else:
          s = set([i[:-1] for i in si if si[i].value > 0.9])

    #print 'start debug'
      #for i in s:
          #print i
      #for i in theta:
          #if theta[i].value>0.9:
              #print i
      #print srcApp
      #print sinkApp
      #print sinkNode

      prevSinkAlg = getPrevAlg(sinkApp,vnf)
      network = ET.Element('network')
      xmlNodes={}
      xmlAlgs={}
      xmlInps={}
      xmlOps={}
      for route in s:
       # if s[route].value>0.9:
          if  allocMEthod == 'heuristic':
               alg,port = route[0]
               src, dst = route[1:3]
          else:
              alg,port,src,dst = route[0:4]
          if allocMEthod ==  'heuristic':
              mapvalueToCheck = theta[ alg,src]
          else:
              mapvalueToCheck =   theta[src,alg].value
          if mapvalueToCheck >0.9: #alg placed on node
               if alg in srcApp:
                   if src not in xmlNodes:
                       xmlNodes[src] = ET.SubElement(network, 'node', pi_id=src)
                   if alg not in xmlAlgs:
                       xmlAlgs[alg] = ET.SubElement(xmlNodes[src], 'algorithm', executable = h.unescape(dictExec[alg]), path = givenPath)
                       print dictParam[alg]
                       ET.SubElement(xmlAlgs[alg], 'parameter', param=h.unescape(dictParam[alg]))
                   if (dst, port) not in xmlOps:
                       xmlOps[dst, port] = ET.SubElement(xmlAlgs[alg], 'output', target_pi_id=str(dst), pipe_id=str(port))
               else:
                   if src not in xmlNodes:
                       xmlNodes[src] = ET.SubElement(network, 'node', pi_id=src)
                   if alg not in xmlAlgs:
                       xmlAlgs[alg] = ET.SubElement(xmlNodes[src], 'algorithm', path = givenPath, executable = h.unescape(dictExec[alg]))
                       ET.SubElement(xmlAlgs[alg], 'parameter', param=str(dictParam[alg]))

                   prevAppsPorts = getPrevAlg(alg,vnf)
                   for prevApp,prevPport in prevAppsPorts:
                       if not allocMEthod == 'heuristic':
                           inpNodes = getSendingNode(src,prevApp,s)
                       else:
                           inpNodes = getSendingNodeHeuristic(src,prevApp,s)
                       #print
                       for inpNode in inpNodes :
                           #print '******************************************debug'
                           #print (inpNode,prevPport,alg)

                           if (inpNode,prevPport,alg) not in xmlInps:
                               xmlInps[inpNode,prevPport,alg]  = ET.SubElement(xmlAlgs[alg],'input', source_pi_id=str(inpNode), pipe_id=str(prevPport))
                           if(dst,port) not in xmlOps:
                               xmlOps[dst,port] = ET.SubElement(xmlAlgs[alg],'output', target_pi_id=str(dst), pipe_id=str(port))

          else: ## forwarding node
              if src not in xmlNodes:
                  xmlNodes[src] = ET.SubElement(network, 'node', pi_id=src)
              if alg not in xmlAlgs:
                  xmlAlgs[alg] = ET.SubElement(xmlNodes[src], 'algorithm', path = givenPath, executable='fwd')
              #inpNode = getSendingNode(src, alg,s)
              if not allocMEthod == 'heuristic':
                  inpNode = getSendingNode(src, alg,s)
              else:
                  inpNode = getSendingNodeHeuristic(src, alg,s)
              print '******************************************debug2', src,alg
              print (inpNode, prevPport, alg)
              if (inpNode, port,alg) not in xmlInps:
                  xmlInps[inpNode, port,alg] = ET.SubElement(xmlAlgs[alg], 'input', source_pi_id=str(inpNode),
                                                              pipe_id=str(port))
              if (dst, port) not in xmlOps:
                      xmlOps[dst, port] = ET.SubElement(xmlAlgs[alg], 'output', target_pi_id=str(dst),
                                                        pipe_id=str(port))
          if dst == sinkNode and (alg,port) in prevSinkAlg: ## sink node
              if dst not in xmlNodes:
                  xmlNodes[dst] = ET.SubElement(network, 'node', pi_id=dst)
              if sinkApp not in xmlAlgs:
                  xmlAlgs[sinkApp] = ET.SubElement(xmlNodes[dst], 'algorithm', path = givenPath, executable=h.unescape(dictExec[sinkApp]))
                  ET.SubElement(xmlAlgs[sinkApp], 'parameter', param=str(dictParam[sinkApp]))

              if (src, port,sinkApp) not in xmlInps:
                  xmlInps[src, port,sinkApp] = ET.SubElement(xmlAlgs[sinkApp], 'input', source_pi_id=str(src),
                                                              pipe_id=str(port))
      tree = ET.ElementTree(network)
      #print(ET.tostring(tree, pretty_print=True))
      # f = open('bin/simParam/allocation.xml', 'w')
      f = open('simParam/allocation.xml', 'w')
      f.write(ET.tostring(tree, pretty_print=True))
      f.close()
      os.system("python xml_viewer.py "+'simParam/allocation.xml'+" &")
#upload = ET.SubElement(connect, 'upload').text="*"
#view = ET.SubElement(network, 'view').text="*"
#delFile = ET.SubElement(network, 'delete_file').text="*"


#for i in theta:

#generate_xml(s,theta,vnf,srcApp,sinkApp,sinkNode)

