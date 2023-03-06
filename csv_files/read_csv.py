import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import hilbert, chirp
import numpy as np

def get_job_PID (df,pid_key):
    """
    Get the jab name per PID

    :param df: dataframe
    :param pid_key: int
    :return:
        str - name of the PID process
    """
    return list(set(df.loc[df["pid"]==pid_key]["job"]))[0]

def get_all_PID(df):
    """
    Get all PIDS in the script

    :param df: Dataframe - output from pandas.read_csv(file.csv)
    :return:
        list of PIDs in the CSV file
    """
    return list(set(df["pid"]))

def get_all_info_keys(df):
    """
    Get all info keys from the dataframe. It maybe helpful for automating plotting
    :param df: data frame from pandas.read_csv
    :return:
        - list of all keys
    """
    return list(df.keys())

def get_info_data(df,pid_key,info_key="cpu_percent"):
    """
    get a the 'info_key' data from a df with a given pid_key
    :param df: Dataframe
    :param pid_key: int: PID number
    :param info_key: str:
    :return:
        - data: list of measured data
    """
    data = list(df.loc[df["pid"]==pid_key][info_key])
    return data


def get_info_data_by_key(df, key, key_string, info_key="cpu_percent"):
    """
    get a the 'info_key' data from a df with a given pid_key
    :param df: Dataframe
    :param pid_key: int: PID number
    :param info_key: str:
    :return:
        - data: list of measured data
    """
    data = list(df.loc[df[key_string]==key][info_key])
    return data


def get_data_envelope(data, use_mean=True):
    """
    return the envelope of measured data (can be mean or median, but probably median will avoid outliers)
    :param data: list of data
    :return:
        - float: median/mean
    """
    if use_mean:
        return np.mean(list(filter(lambda a: a!=0,data)))
    else:
        return np.median(list(filter(lambda a: a!=0,data)))


def print_network_delay_per_link_dxcp(df, pids, time_offsets = []):
    """
    :param df:
    :param pids: list of pids in order read_data, read_data, dxcp_phat, print_rersults
    :return:
    """
    time_in = {pid: sorted(get_info_data_by_key(df, pid, "pid", info_key = "time in")) for pid in pids}
    time_out = {pid: sorted(get_info_data_by_key(df, pid, "pid", info_key = "time out")) for pid in pids}

    if time_offsets == []:
        time_offsets = [0 for i in range(len(pids))]


    delays = []
    delay_per_link = {}
    ''' I do not think this is correct!!'''
    i = 0
   # while i < len(time_in.get(pids[0])):
    #    delays.append(time_in[pids[2]][i] - time_out[pids[0]][i] + time_offsets[2] - time_offsets[0])
     #   delays.append(time_in[pids[2]][i] - time_out[pids[1]][i]+ time_offsets[2] - time_offsets[1])
      #  delays.append(time_in[pids[3]][i] - time_out[pids[2]][i]+ time_offsets[3] - time_offsets[2])
       # i += 1
    links = [(0,2),(1,2),(2,3)]
    for s,r in links:
        delay_per_link[f'{s}-{r}']=(np.array(time_in[pids[r]],dtype=np.float64) - np.array(time_out[pids[s]] ,dtype=np.float64))/ 1000000 + time_offsets[r] - time_offsets[s]
        print(f"mean delay for link {get_job_PID(df,pids[s]),get_job_PID(df,pids[r])} = {np.mean(delay_per_link[f'{s}-{r}'])}'ms'")
    #print("mean delay", np.mean(delays) / 1000000, 'ms')
    return delay_per_link



def print_network_delay_per_link_source_separation(df, pids, time_offsets = []):
    """
     :param df:
     :param pids: list of pids in order ica_readModule, ica_readModule, cov1svd, whiten, normfn, cov2svd
     :return:
     """
    time_in = {pid: get_info_data_by_key(df, pid, "pid", info_key="time in") for pid in pids}
    time_out = {pid: get_info_data_by_key(df, pid, "pid", info_key="time out") for pid in pids}

    if time_offsets == []:
        time_offsets = [0 for i in range(len(pids))]

    # delays = []
    # i = 0
    # while i < len(time_in.get(pids[0])):
    #     #ica_readModule -> cov1svd
    #     delays.append(time_in[pids[2]][i] - time_out[pids[0]][i])
    #     delays.append(time_in[pids[2]][i] - time_out[pids[1]][i])
    #     #cov1svd -> whiten
    #     delays.append(time_in[pids[3]][i] - time_out[pids[2]][i])
    #     #whiten-> normfn
    #     delays.append(time_in[pids[4]][i] - time_out[pids[3]][i])
    #     #whiten -> cov2svd
    #     delays.append(time_in[pids[5]][i] - time_out[pids[3]][i])
    #     #normfn -> cov2svd
    #     delays.append(time_in[pids[5]][i] - time_out[pids[4]][i])
    #     i += 1
    # print(np.mean(delays) / 1000000,'ms')

    links = [(0,2),(1,2),(2,3),(3,4),(3,5),(4,5)]
    cols = [(get_job_PID(df,pids[s]),get_job_PID(df,pids[r])) for s,r in links]
    print("cols = ", cols)
    delay_per_link={}
    for s,r in links:
        delay_per_link[f'{s}-{r}']=np.array(time_in[pids[r]])/1000000 - np.array(time_out[pids[s]])/ 1000000 + time_offsets[r] - time_offsets[s]
        print(f"mean delay for link {get_job_PID(df,pids[s]),get_job_PID(df,pids[r])} = {np.median(delay_per_link[f'{s}-{r}'])}'ms'")

    return delay_per_link


def print_network_delay_end_to_end(df, pids, hopdistance,  time_offsets = [0,0]):
    time_in = get_info_data_by_key(df, pids[0], "pid", info_key="time in")
    time_out = get_info_data_by_key(df, pids[1], "pid", info_key="time in")


    delays = []
    i = 0
    while i + hopdistance < len(time_in):
        delays.append((time_out[i+hopdistance] - time_in[i])/1000000 + time_offsets[0] - time_offsets[1])
        i += 1

    print(np.mean(delays),'ms')






## Plot data with envelope

    


df = pd.read_csv (r'DXCP/adhoc_centralized/file7.csv')
'''
1056: read_data -3.273
1054: read_data +1.198
1055: dxcp_phat -0.048 
1111: print_results -0.048
'''
print("***** DXCP/adhoc_centralized *******")
delay_adhoc_centralized = print_network_delay_per_link_dxcp(df, [1056, 1054, 1055, 1111],
                                                            time_offsets=[ -3.273, 1.198, -0.048, -0.048])
print_network_delay_end_to_end(df, [41056,1111], 2)


df = pd.read_csv (r'DXCP/adhoc_distributed/file7.csv')
'''
983: read_data -0.902
981: read_data +0.778
978: dxcp_phat +0.043
966: print_results -0.377
'''
print("***** DXCP/adhoc_distributed *******")
delay_adhoc_dist = print_network_delay_per_link_dxcp(df, [983,981,978,966],
                                                     time_offsets=[0.778, -0.902, 0.043, -0.377])
print_network_delay_end_to_end(df, [983,966], 2)

df = pd.read_csv (r'DXCP/infrastructure_distributed/file7.csv')
'''
3281: read_data
3234: read_data
3462: dxcp_phat
3487: print_results
'''
print("***** DXCP/infrastructure_distributed *******")
delay_infra_dist =print_network_delay_per_link_dxcp(df, [3281, 3234, 3462, 3487],
                                                    time_offsets=[3.291, 0.572,  -1.691, 0.384])
print_network_delay_end_to_end(df, [3281, 3487], 2)

## print table for the results
from tabulate import tabulate
cols = ["adhoc_centralized", "adhoc_distributed","infrastructure_distributed"]
rows = [('read_data', 'dxcp_phat') ,('read_data', 'dxcp_phat') ,('dxcp_phat', 'print_results')]
data = np.array(
                [
                [rows[0],np.mean(delay_adhoc_centralized[f'{0}-{2}']),np.mean(delay_adhoc_dist[f'{0}-{2}']),np.mean(delay_infra_dist[f'{0}-{2}'])],
                [rows[1],np.mean(delay_adhoc_centralized[f'{1}-{2}']),np.mean(delay_adhoc_dist[f'{1}-{2}']),np.mean(delay_infra_dist[f'{1}-{2}'])],
                [rows[2],np.mean(delay_adhoc_centralized[f'{2}-{3}']),np.mean(delay_adhoc_dist[f'{2}-{3}']),np.mean(delay_infra_dist[f'{2}-{3}'])]
                ]
)
print(tabulate(data,headers=cols,tablefmt='latex'))
print(tabulate(data,headers=cols,tablefmt='pipe'))

df = pd.read_csv (r'source_separation/adhoc_centralized/file7.csv')
'''
1223 : cov2svd
1224 : normfn
1225 : cov1svd +0.278
1226 : whiten 
1130 : ica_readmodule +0.970
1124 : ica_readmodule -0.482
'''
print("***** source_separation/adhoc_centralized *******")
delay_adhoc_centralized = print_network_delay_per_link_source_separation(df, [1130, 1124, 1225, 1226, 1224, 1223],
                                                                         time_offsets=[-0.482, 0.970, 0.278, 0.278, 0.278, 0.278])
print_network_delay_end_to_end(df, [1130, 1223], 4)

df = pd.read_csv (r'source_separation/adhoc_distributed/file7.csv')
'''
1313 : normfn +0.278
1185 : whiten -0.649
1316 : cov2svd +0.278
1186 : cov1svd -0.649
1167 : ica_readmodule -0.191
1160 : ica_readmodule 0.970
'''
print("***** source_separation/adhoc_distributed *******")
delay_adhoc_dist = print_network_delay_per_link_source_separation(df, [1167, 1160, 1186, 1185, 1313, 1316],
                                                                  time_offsets=[-0.191, 0.970, -0.649 ,-0.649, 0.278, 0.278])
print_network_delay_end_to_end(df, [1167, 1316], 4)

df = pd.read_csv (r'source_separation/infrastructure_distributed/file7.csv')

in_1 = get_info_data(df,5630,info_key="time in")
in_2 = get_info_data(df,5641,info_key="time in")
in_3 = get_info_data(df,5592,info_key="time in")
    
out_1 = get_info_data(df,5630,info_key="time out")
out_2 = get_info_data(df,5641,info_key="time out")
out_3 = get_info_data(df,5592,info_key="time out")

    



'''
3054 : ica_readmodule +2.291
3006 : ica_readmodule +0.572
3244 : cov2svd +0.169
3215 : cov1svd -1.691
3242 : normfn +0.169
3214 : whiten -1.691
'''
# all_pids = get_all_PID(df)
# for i in all_pids:
#       print(i,':',get_job_PID(df,i))
print("***** source_separation/infrastructure_distributed *******")
delay_infra_dist = print_network_delay_per_link_source_separation(df, [3054, 3006, 3215, 3214, 3242, 3244],
                                                                  time_offsets=[0.572, 2.291, -1.691, -1.691, 0.169, 0.169])
print_network_delay_end_to_end(df, [3054,3244], 4)


rows =  [('ica_readmodule', 'cov1svd'), ('ica_readmodule', 'cov1svd'), ('cov1svd', 'whiten'), ('whiten', 'normfn'), ('whiten', 'cov2svd'), ('normfn', 'cov2svd')]
cols = ["adhoc_centralized", "adhoc_distributed","infrastructure_distributed"]
links = [(0, 2), (1, 2), (2, 3), (3, 4), (3, 5), (4, 5)]

data = np.array([
    [rows[i], np.mean(delay_adhoc_centralized[f'{links[i][0]}-{links[i][1]}']), np.mean(delay_adhoc_dist[f'{links[i][0]}-{links[i][1]}']),
     np.mean(delay_infra_dist[f'{links[i][0]}-{links[i][1]}'])] for i in range(len(links))
])
print(tabulate(data,headers=cols,tablefmt='latex'))
print(tabulate(data,headers=cols,tablefmt='pipe'))

# all_pids = get_all_PID(df)
# pid_to_test = all_pids[0]
# data_key ='cpu_percent'
# measured_data = get_info_data(df,pid_to_test,data_key)
# data_envelope = get_data_envelope(measured_data)
# #TODO: need to add time stamps? probably not needed for the paper
# plt.plot(measured_data,label='measured')
# plt.plot(data_envelope*np.ones(len(measured_data)),label='profile')
# plt.title(f"Profiling PID = {pid_to_test} : {get_job_PID(df,pid_to_test)}")
# plt.ylabel(data_key)
# plt.show()
#
