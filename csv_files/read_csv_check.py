import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import scipy
from GPy.plotting.plotly_dep.defaults import yerrorbar
import tikzplotlib
import matplotlib as mpl

mpl.rcParams.update(mpl.rcParamsDefault)

font = {'family' : 'normal',
        # 'weight' : 'bold',
        'size'   : 22}

matplotlib.rc('font', **font)

from scipy.signal import hilbert, chirp
import numpy as np
from tabulate import tabulate


def get_job_PID(df, pid_key):
    """
    Get the jab name per PID

    :param df: dataframe
    :param pid_key: int
    :return:
        str - name of the PID process
    """
    return list(set(df.loc[df["pid"] == pid_key]["job"]))[0]


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


def get_info_data(df, pid_key, info_key="cpu_percent"):
    """
    get a the 'info_key' data from a df with a given pid_key
    :param df: Dataframe
    :param pid_key: int: PID number
    :param info_key: str:
    :return:
        - data: list of measured data
    """
    data = list(df.loc[df["pid"] == pid_key][info_key])
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
    data = list(df.loc[df[key_string] == key][info_key])
    return data


def get_data_envelope(data, use_mean=True):
    """
    return the envelope of measured data (can be mean or median, but probably median will avoid outliers)
    :param data: list of data
    :return:
        - float: median/mean
    """
    if use_mean:
        return np.mean(list(filter(lambda a: a != 0, data)))
    else:
        return np.median(list(filter(lambda a: a != 0, data)))


def print_network_delay_per_link_dxcp(df, pids, time_offsets=[]):
    """
    :param df:
    :param pids: list of pids in order read_data, read_data, dxcp_phat, print_rersults
    :return:
    """
    time_in = {pid: sorted(get_info_data_by_key(df, pid, "pid", info_key="time in")) for pid in pids}
    time_out = {pid: sorted(get_info_data_by_key(df, pid, "pid", info_key="time out")) for pid in pids}

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
    links = [(0, 2), (1, 2), (2, 3)]
    for s, r in links:
        delay_per_link[f'{s}-{r}'] = (np.array(time_in[pids[r]], dtype=np.float64) - np.array(time_out[pids[s]],
                                                                                              dtype=np.float64)) / 1000000 + \
                                     time_offsets[r] - time_offsets[s]
        print(
            f"mean delay for link {get_job_PID(df, pids[s]), get_job_PID(df, pids[r])} = {np.median(list(filter(lambda a: a != 0, delay_per_link[f'{s}-{r}'])))} or {np.mean(delay_per_link[f'{s}-{r}'])}'ms'")

        # plt.figure()
        # plt.plot(delay_per_link[f'{s}-{r}'],
        #          label=f"link {get_job_PID(df, pids[s]), get_job_PID(df, pids[r])}")
        # plt.legend()

    # print("mean delay", np.mean(delays) / 1000000, 'ms')
    return delay_per_link


def print_network_delay_per_link_source_separation(df, pids, time_offsets=[]):
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

    links = [(0, 2), (1, 2), (2, 3), (3, 4), (3, 5), (4, 5)]
    cols = [(get_job_PID(df, pids[s]), get_job_PID(df, pids[r])) for s, r in links]
    print("cols = ", cols)
    delay_per_link = {}
    for s, r in links:
        delay_per_link[f'{s}-{r}'] = np.array(time_in[pids[r]]) / 1000000 - np.array(time_out[pids[s]]) / 1000000 + \
                                     time_offsets[r] - time_offsets[s]
        print(
            f"mean delay for link {get_job_PID(df, pids[s]), get_job_PID(df, pids[r])} = {np.median(delay_per_link[f'{s}-{r}'])}'ms'")

        # plt.figure()
        #
        # plt.plot(delay_per_link[f'{s}-{r}'],
        #          label=f"link {get_job_PID(df, pids[s]), get_job_PID(df, pids[r])}")
        # plt.legend()


    return delay_per_link



def print_network_delay_end_to_end(df, pids, hopdistance, time_offsets=[0, 0]):
    time_in = get_info_data_by_key(df, pids[0], "pid", info_key="time in")
    time_out = get_info_data_by_key(df, pids[1], "pid", info_key="time in")

    delays = []
    i = 0
    while i + hopdistance < len(time_in):
        delays.append((time_out[i + hopdistance] - time_in[i]) / 1000000 + time_offsets[0] - time_offsets[1])
        i += 1

    print(np.mean(delays), 'ms')
    print(np.median(delays), 'ms')
    # print(np.max(delays), 'ms')

def print_processing_data(df):
    all_pids = get_all_PID(df)
    time_in = {i: sorted(get_info_data_by_key(df, i, "pid", info_key="time in")) for i in all_pids}
    time_out = {i: sorted(get_info_data_by_key(df, i, "pid", info_key="time out")) for i in all_pids}
    processing_time = {i: np.array(time_out[i]) - np.array(time_in[i]) for i in all_pids}
    processing_data = [[get_job_PID(df, i),
                        np.max(processing_time[i])/1e6,
                        np.mean(processing_time[i])/1e6,
                        np.median(processing_time[i])/1e6,
                        get_confidence_interval_err(processing_time[i])/1e6] for i in processing_time]
    print(tabulate(processing_data, tablefmt='pipe',headers=['job','max','mean','median','CI']))
    return ({get_job_PID(df, i):np.mean(processing_time[i])/1e6 for i in processing_time},{get_job_PID(df, i):get_confidence_interval_err(processing_time[i])/1e6 for i in processing_time})


def bar_plot(barst,err_data,scenarios,apps,processing_time=None,processing_time_CI=None,barWidth=0.2):
    rt= range(len(apps))
    locs = ["upper left", "lower left", "center right"]

    for i in range(len(scenarios)):
        if scenarios[i]!="centralized":
            plt.bar(np.array(rt)+i*barWidth, barst[:,i], width=barWidth, label=scenarios[i],
                    yerr=err_data[:,i][:,-1]-err_data[:,i][:,-2],bottom=0)
        else:
            plt.bar(rt[0]+i*barWidth, barst[0,i], width=barWidth, label=scenarios[i],
                    yerr=err_data[0,i][-1]-err_data[0,i][-2],bottom=0)


    if processing_time!=None:
        bar_process = [processing_time[i] for i in apps]
        plt.bar(np.array(rt)+(i+1)*barWidth,bar_process, width=barWidth, label="CPU_time",yerr=[processing_time_CI[i] for i in apps], bottom=0)
    # plt.legend(  loc="center left", bbox_to_anchor=(1,1))
    apps = [i if i!="print_results" else "interpolate" for i in apps]
    apps = [i if i!="dxcp_phat" else "X-Corr" for i in apps]
    apps = [i if i!="cov1svd"  else "Cov1" for i in apps]
    apps = [i if  i!="cov2svd" else "Cov2" for i in apps]
    apps = [i if i!="normfn" else "norm" for i in apps]
    plt.xticks([r+1.5*barWidth  for r in range(len(rt))],
               [apps[i] for i in range(len(rt))], rotation=0)
    # plt.tight_layout()
    plt.ylabel("Delay(ms)")
    # plt.show()
    plt.legend(bbox_to_anchor=(0.5, 1.22), loc='center', borderaxespad=0., ncol=2)
    plt.tight_layout()
    plt.gca().set_ylim(bottom=0)

    # plt.show()


    # plt.subplots_adjust(bottom=0.2, top=0.98)

def print_e2e_delay(df,exp="dxcp",mean=True):
    all_pids = get_all_PID(df)
    # all_pids=all_pids[2:]
    f_ids = []
    if exp=="ica":
        start_task = "ica_readmodule"
        end_task = "cov2svd"
    elif exp=="dxcp":
        start_task = "read_data 0"
        end_task = "print_results"
    for i in all_pids:
        print(i, ':', get_job_PID(df, i))
        if get_job_PID(df, i) == start_task:
            time_out_start = np.array(get_info_data_by_key(df, i, "pid", info_key="time out")) / 1e6
        elif get_job_PID(df, i) == end_task:
            time_out_end = np.array(get_info_data_by_key(df, i, "pid", info_key="time out")) / 1e6

    print(f"mean: {np.mean(time_out_end - time_out_start)}\n"
          f"median: {np.median(time_out_end - time_out_start)}\n"
          )
    if mean:
        return np.mean(time_out_end - time_out_start)
    else:
        return np.median(time_out_end - time_out_start)

def print_e2e_boxPlot(df,exp="dxcp",):
    all_pids = get_all_PID(df)
    # all_pids=all_pids[2:]
    f_ids = []
    if exp=="ica":
        start_task = "ica_readmodule"
        end_task = "cov2svd"
    elif exp=="dxcp":
        start_task = "read_data 0"
        end_task = "print_results"
    for i in all_pids:
        print(i, ':', get_job_PID(df, i))
        if get_job_PID(df, i) == start_task:
            time_out_start = np.array(get_info_data_by_key(df, i, "pid", info_key="time out")) / 1e6
        elif get_job_PID(df, i) == end_task:
            time_out_end = np.array(get_info_data_by_key(df, i, "pid", info_key="time out")) / 1e6

    print(f"mean: {np.mean(time_out_end - time_out_start)}\n"
          f"median: {np.median(time_out_end - time_out_start)}\n"
          )

    return time_out_end - time_out_start


def print_e2e_std(df,exp="dxcp"):
    all_pids = get_all_PID(df)
    # all_pids=all_pids[2:]
    f_ids = []
    if exp=="ica":
        start_task = "ica_readmodule"
        end_task = "cov2svd"
    elif exp=="dxcp":
        start_task = "read_data 0"
        end_task = "print_results"
    for i in all_pids:
        if get_job_PID(df, i) == start_task:
            time_out_start = np.array(get_info_data_by_key(df, i, "pid", info_key="time out")) / 1e6
        elif get_job_PID(df, i) == end_task:
            time_out_end = np.array(get_info_data_by_key(df, i, "pid", info_key="time out")) / 1e6


    return np.std(time_out_end - time_out_start)

def mean_confidence_interval(data, confidence=0.75,mean=False):
    a = 1.0 * np.array(data)
    n = len(a)
    if mean:
        m, se = np.mean(a), scipy.stats.sem(a)
    else:
        m, se = np.median(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    return m, m-h, m+h



def get_confidence_interval_err(data, confidence=0.75,mean=False):
    a = 1.0 * np.array(data)
    n = len(a)
    if mean:
        m, se = np.mean(a), scipy.stats.sem(a)
    else:
        m, se = np.median(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    return h


### print processing time
df = pd.read_csv(r'source_separation/infrastructure_distributed/file7.csv')
all_pids = get_all_PID(df)
# all_pids=all_pids[2:]
f_ids=[]
# start_task="ica_readmodule"
# end_task= "cov2svd"
# for i in all_pids:
#       print(i,':',get_job_PID(df,i))
#       if get_job_PID(df,i)==start_task:
#           time_out_start = np.array(get_info_data_by_key(df, i, "pid", info_key="time out"))/1e6
#       elif get_job_PID(df,i)==end_task:
#           time_out_end = np.array(get_info_data_by_key(df, i, "pid", info_key="time out"))/1e6
#
# print(f"mean: {np.mean(time_out_end-time_out_start)}\n"
#       f"median: {np.median(time_out_end-time_out_start)}\n"
#       f"max: {np.max(time_out_end-time_out_start)}")
# e2e_delay = np.mean(time_out_end-time_out_start)
df = pd.read_csv(r'DXCP/adhoc_centralized/file7.csv')
dxcp_adhoc_centralized = print_e2e_delay(df)
data1 = print_e2e_boxPlot(df)

df = pd.read_csv(r'DXCP/adhoc_distributed/file7.csv')
dxcp_adhoc_distributed =print_e2e_delay(df)
data2 = print_e2e_boxPlot(df)

df = pd.read_csv(r'DXCP/infrastructure_distributed/file7.csv')
dxcp_infrastructure_distributed =print_e2e_delay(df)
data3 = print_e2e_boxPlot(df)

raw_data = [data1,data2,data3]
plt.figure()
plt.boxplot(raw_data, showfliers=False)
plt.xticks(range(1,4),["centralized","mesh-distributed","AP-distributed"])
plt.ylabel("Delay(ms)")
plt.show()
e2e_dxcp =[
    [
        print_e2e_delay(pd.read_csv(r'DXCP/adhoc_centralized/file7.csv'),mean=False),
        print_e2e_delay(pd.read_csv(r'DXCP/adhoc_distributed/file7.csv'),mean=False),
        print_e2e_delay(pd.read_csv(r'DXCP/infrastructure_distributed/file7.csv'),mean=False)
    ]
]
print(tabulate(e2e_dxcp,tablefmt='pipe',headers=['adhoc_centralized','adhoc_distributed','infrastructure_distributed']))
print(tabulate(e2e_dxcp,tablefmt='latex',headers=['adhoc_centralized','adhoc_distributed','infrastructure_distributed']))

# std_dxcp = [
#     [
#         print_e2e_std(pd.read_csv(r'DXCP/adhoc_centralized/file7.csv')),
#         print_e2e_std(pd.read_csv(r'DXCP/adhoc_distributed/file7.csv')),
#         print_e2e_std(pd.read_csv(r'DXCP/infrastructure_distributed/file7.csv'))
#     ]
# ]
# print(tabulate(std_dxcp,tablefmt='pipe',headers=['adhoc_centralized','adhoc_distributed','infrastructure_distributed']))


print("\n**** ICA ****\n")
df = pd.read_csv(r'source_separation/adhoc_centralized/file7.csv')
print_e2e_delay(df,exp='ica')
data1 = print_e2e_boxPlot(df,exp='ica')

df = pd.read_csv(r'source_separation/adhoc_distributed/file7.csv')
print_e2e_delay(df,exp='ica')
data2 = print_e2e_boxPlot(df,exp='ica')

df = pd.read_csv(r'source_separation/infrastructure_distributed/file7.csv')
print_e2e_delay(df,exp='ica')
data3 = print_e2e_boxPlot(df,exp='ica')

raw_data=[data1,data2,data3]
plt.figure()
plt.boxplot(raw_data, showfliers=False)
plt.xticks(range(1,4),["centralized","mesh-distributed","AP-distributed"])
plt.ylabel("Delay(ms)")
plt.show()

# all_pids=f_ids


# for i in processing_time:
#     plt.figure()
#     plt.plot(processing_time[i],label=get_job_PID(df,i))
#     plt.legend()
# plt.show()


## Plot data with envelope


df = pd.read_csv(r'DXCP/adhoc_centralized/file7.csv')
print_processing_data(df)


'''
1056: read_data -3.273
1054: read_data +1.198
1055: dxcp_phat -0.048 
1111: print_results -0.048
'''
print("***** DXCP/adhoc_centralized *******")
delay_adhoc_centralized = print_network_delay_per_link_dxcp(df, [1056, 1054, 1055, 1111],
                                                            time_offsets=[-3.273, 1.198, -0.048, -0.048])
print_network_delay_end_to_end(df, [41056, 1111], 2)

df = pd.read_csv(r'DXCP/adhoc_distributed/file7.csv')
'''
983: read_data -0.902
981: read_data +0.778
978: dxcp_phat +0.043
966: print_results -0.377
'''
print_processing_data(df)
print("***** DXCP/adhoc_distributed *******")
delay_adhoc_dist = print_network_delay_per_link_dxcp(df, [983, 981, 978, 966],
                                                     time_offsets=[0.778, -0.902, 0.043, -0.377])
print_network_delay_end_to_end(df, [983, 966], 2)

df = pd.read_csv(r'DXCP/infrastructure_distributed/file7.csv')
'''
3281: read_data
3234: read_data
3462: dxcp_phat
3487: print_results
'''

print("***** DXCP/infrastructure_distributed *******")
print_processing_data(df)

delay_infra_dist = print_network_delay_per_link_dxcp(df, [3281, 3234, 3462, 3487],
                                                     time_offsets=[3.291, 0.572, -1.691, 0.384])
print_network_delay_end_to_end(df, [3281, 3487], 2)

## print table for the results

# links = [(0,2),(1,2),(2,3)]
links = [(0,2),(1,2),(2,3)]
cols = ["adhoc_centralized", "adhoc_distributed", "infrastructure_distributed"]
rows = [('read_data', 'dxcp_phat'), ('read_data', 'dxcp_phat'), ('dxcp_phat', 'print_results')]
data = np.array(
    [
        [rows[0], np.median(delay_adhoc_centralized[f'{0}-{2}']), np.median(delay_adhoc_dist[f'{0}-{2}']),
         np.median(delay_infra_dist[f'{0}-{2}'])],
        [rows[1], np.median(delay_adhoc_centralized[f'{1}-{2}']), np.median(delay_adhoc_dist[f'{1}-{2}']),
         np.median(delay_infra_dist[f'{1}-{2}'])],
        [rows[2], np.median(delay_adhoc_centralized[f'{2}-{3}']), np.median(delay_adhoc_dist[f'{2}-{3}']),
         np.median(delay_infra_dist[f'{2}-{3}'])]
    ]
)
print(tabulate(data, headers=cols, tablefmt='latex'))
print(tabulate(data, headers=cols, tablefmt='pipe'))

## Bar plot DXCP
# plt.close('all')
plt.figure()
rowss = [('read_data', 'dxcp_phat'),
         # ('read_data', 'dxcp_phat'),
         ('dxcp_phat', 'print_results')]

linkss = [(0,2),
         # (1,2),
         (2,3)]

bar_data = np.array([
    [np.median(delay_adhoc_centralized[f'{linkss[i][0]}-{linkss[i][1]}']),
     np.median(delay_adhoc_dist[f'{linkss[i][0]}-{linkss[i][1]}']),
     np.median(delay_infra_dist[f'{linkss[i][0]}-{linkss[i][1]}'])] for i in range(len(linkss))
])



err_data =  np.array([
    [mean_confidence_interval(delay_adhoc_centralized[f'{linkss[i][0]}-{linkss[i][1]}'],mean=False),
     mean_confidence_interval(delay_adhoc_dist[f'{linkss[i][0]}-{linkss[i][1]}'],mean=False),
     mean_confidence_interval(delay_infra_dist[f'{linkss[i][0]}-{linkss[i][1]}'],mean=False)] for i in range(len(linkss))
])

apps = [rowss[i][1] for i in range(len(rowss))]
scenarios = ["centralized", "mesh_distributed", "AP_distributed"]
processing_time,processing_time_CI = print_processing_data(df)
del processing_time['read_data 1']
bar_plot(bar_data,err_data,scenarios,apps,processing_time,processing_time_CI)
plt.savefig("dxcp_delay.pdf")
tikzplotlib.save("dxcp_delay.tex")

df = pd.read_csv(r'source_separation/adhoc_centralized/file7.csv')
'''
1223 : cov2svd
1224 : normfn
1225 : cov1svd +0.278
1226 : whiten 
1130 : ica_readmodule +0.970
1124 : ica_readmodule -0.482
'''
print("***** source_separation/adhoc_centralized *******")
print_processing_data(df)
delay_adhoc_centralized = print_network_delay_per_link_source_separation(df, [1130, 1124, 1225, 1226, 1224, 1223],
                                                                         time_offsets=[-0.482, 0.970, 0.278, 0.278,
                                                                                       0.278, 0.278])
print_network_delay_end_to_end(df, [1130, 1223], 4)

df = pd.read_csv(r'source_separation/adhoc_distributed/file7.csv')
'''
1313 : normfn +0.278
1185 : whiten -0.649
1316 : cov2svd +0.278
1186 : cov1svd -0.649
1167 : ica_readmodule -0.191
1160 : ica_readmodule 0.970
'''
print("***** source_separation/adhoc_distributed *******")
print_processing_data(df)

delay_adhoc_dist = print_network_delay_per_link_source_separation(df, [1167, 1160, 1186, 1185, 1313, 1316],
                                                                  time_offsets=[-0.191, 0.970, -0.649, -0.649, 0.278,
                                                                                0.278])
print_network_delay_end_to_end(df, [1167, 1316], 4)

df = pd.read_csv(r'source_separation/infrastructure_distributed/file7.csv')

in_1 = get_info_data(df, 5630, info_key="time in")
in_2 = get_info_data(df, 5641, info_key="time in")
in_3 = get_info_data(df, 5592, info_key="time in")

out_1 = get_info_data(df, 5630, info_key="time out")
out_2 = get_info_data(df, 5641, info_key="time out")
out_3 = get_info_data(df, 5592, info_key="time out")

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
print_processing_data(df)

delay_infra_dist = print_network_delay_per_link_source_separation(df, [3054, 3006, 3215, 3214, 3242, 3244],
                                                                  time_offsets=[0.572, 2.291, -1.691, -1.691, 0.169,
                                                                                0.169])
print_network_delay_end_to_end(df, [3054, 3244], 4)

# plt.close('all')

rows = [('ica_readmodule', 'cov1svd'),
        ('ica_readmodule', 'cov1svd'),
        ('cov1svd', 'whiten'),
        ('whiten', 'normfn'),
        ('whiten', 'cov2svd'),
        ('normfn', 'cov2svd')]
cols = ["adhoc_centralized", "adhoc_distributed", "infrastructure_distributed"]
links = [(0, 2), (1, 2), (2, 3), (3, 4), (3, 5), (4, 5)]

data = np.array([
    [rows[i], np.median(delay_adhoc_centralized[f'{links[i][0]}-{links[i][1]}']),
     np.median(delay_adhoc_dist[f'{links[i][0]}-{links[i][1]}']),
     np.median(delay_infra_dist[f'{links[i][0]}-{links[i][1]}'])] for i in range(len(links))
])

## Bar plot ICA
plt.figure()
linkss = [(0, 2),
         # (1, 2),
         # (2, 3),
         (3, 4),
         (3, 5),
         # (4, 5)
         ]

bar_data = np.array([
    [np.median(delay_adhoc_centralized[f'{linkss[i][0]}-{linkss[i][1]}']),
     np.median(delay_adhoc_dist[f'{linkss[i][0]}-{linkss[i][1]}']),
     np.median(delay_infra_dist[f'{linkss[i][0]}-{linkss[i][1]}'])] for i in range(len(linkss))
])
err_data = np.array([
    [mean_confidence_interval(delay_adhoc_centralized[f'{linkss[i][0]}-{linkss[i][1]}'],mean=False),
     mean_confidence_interval(delay_adhoc_dist[f'{linkss[i][0]}-{linkss[i][1]}'],mean=False),
     mean_confidence_interval(delay_infra_dist[f'{linkss[i][0]}-{linkss[i][1]}'],mean=False)] for i in range(len(linkss))
])
rows = [('ica_readmodule', 'cov1svd'),
        # ('ica_readmodule', 'cov1svd'),
        # ('cov1svd', 'whiten'),
        ('whiten', 'normfn'),
        ('whiten', 'cov2svd'),
        # ('normfn', 'cov2svd')
        ]
apps = [rows[i][1] for i in range(len(linkss))]
scenarios = ["centralized", "mesh_distributed", "AP_distributed"]
processing_time,processing_time_CI = print_processing_data(df)
bar_plot(bar_data,err_data,scenarios,apps,processing_time,processing_time_CI)
plt.savefig("ica_delay.pdf")
tikzplotlib.save("ica_delay.tex")

# plt.figure()
# bar_data = np.array([
#     [np.mean(delay_adhoc_centralized[f'{links[i][0]}-{links[i][1]}']),
#      np.mean(delay_adhoc_dist[f'{links[i][0]}-{links[i][1]}']),
#      np.mean(delay_infra_dist[f'{links[i][0]}-{links[i][1]}'])] for i in range(len(links))
# ])
#
# bar_plot(bar_data,scenarios,apps,processing_time)

print(tabulate(data, headers=cols, tablefmt='latex'))
print(tabulate(data, headers=cols, tablefmt='pipe'))

e2e_source_separation =[
    [
        print_e2e_delay(pd.read_csv(r'source_separation/adhoc_centralized/file7.csv'),exp='ica'),
        print_e2e_delay(pd.read_csv(r'source_separation/adhoc_distributed/file7.csv'),exp='ica'),
        print_e2e_delay(pd.read_csv(r'source_separation/infrastructure_distributed/file7.csv'),exp='ica')
    ]
]
print(tabulate(e2e_source_separation,tablefmt='pipe',headers=['adhoc_centralized','adhoc_distributed','infrastructure_distributed']))
print(tabulate(e2e_source_separation,tablefmt='latex',headers=['adhoc_centralized','adhoc_distributed','infrastructure_distributed']))


# plt.show()



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
