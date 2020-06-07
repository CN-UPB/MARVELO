
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