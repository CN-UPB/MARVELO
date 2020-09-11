
# How to use

## Install required packages

 - Download [gurobi solver](https://www.gurobi.com/) and get a [free academic liscence](https://www.gurobi.com/downloads/end-user-license-agreement-academic/)
 - Install pyomo interface: pip install pyomo

## Run MARVELO 
 python gen_randParam_modified.py
 
## Quick Description
- gen_randParam_modified.py: generate a random network and a linear overlay graph. Then set some simulation params and runs MARVELO. 
- multiGraphVNEPower: solves the embedding problem
- convertResults.py example on how to read the output 
- param: A folder which contains the input graphs to MARVELO
- results: a folder containing the results from MARVELO in pickle format
- resultsTxt: a helper folder for convertResults.py 

### Examples of parameters files
Check file [pos411.csv](param/pos411.csv)
### Position of the nodes

|      |A                            |B     |C   |D   |
|------|-----------------------------|------|----|----|
|0     |0.0                          |0.0   |25.0|25.0|
|1     |0.0                          |25.0  |0.0 |25.0|


 - 1st row - nodes ID
 - 2nd row - x coordinates
 - 3rd row - y coordinates
### Attenuation - arcsfile
Check file [a411.csv](param/a411.csv)

| |Start                        |End   |Attenuation                                  |
|------|-----------------------------|------|---------------------------------------------|
|0     |A                            |B     |0.0016                                       |
|1     |A                            |C     |0.0016                                       |
|2     |A                            |D     |0.0007999999999999999                        |

 - Start: sending node
 - End: receiving node 
 - Attenuation: attenuation from the sending node at the receiving one

### Block demands - appSimFile
Check file [b311.csv](param/b411.csv)

| |srcapp                       |port  |demand                                       |
|------|-----------------------------|------|---------------------------------------------|
|1     |2                            |1     |20                                           |
                                          |

Block 1 which has output port 1 demands 20 resources

### Avaialble resources - nodesfile
Check file [n411.csv](param/n411.csv)

| |Node                         |capacity|
|------|-----------------------------|--------|
|0     |A                            |21      |
|1     |B                            |21      |

Nodes A and B have at maximum 21 resources 


### Overlay graph - chainsfile
Check file [chain_linear_3.csv](param/chain_linear_3.csv)

| |srcapp                       |srcport|dstapp|
|------|-----------------------------|-------|------|
|0     |1                            |1      |2     |
|1     |2                            |1      |3     |

Connected as follow 
1->2->3

where blocks 1 and 2 have only one outputs (srcport)

If you want to pass your own csv files, use the function `runMarvelo` as in [here](https://github.com/CN-UPB/MARVELO/blob/d87f8637439e0892df1a1afc19c0a2c71852003e/Documentation/marvelo_example/gen_randParam_modified.py#L298)



