
import time
import matplotlib.pyplot as plt
import numpy as np


def get_memory(t):
    "Simulate a function that returns system memory"
    return 100 * (0.5 + 0.5 * np.sin(0.5 * np.pi * t))


def get_cpu(t):
    "Simulate a function that returns cpu usage"
    return 100 * (0.5 + 0.5 * np.sin(0.2 * np.pi * (t - 0.25)))


def get_net(t):
    "Simulate a function that returns network bandwidth"
    return 100 * (0.5 + 0.5 * np.sin(0.7 * np.pi * (t - 0.1)))


def get_stats(t):
    return get_memory(t), get_cpu(t), get_net(t)

fig, ax = plt.subplots()
ind = np.arange(1, 5)

# show the figure, but do not block

processDelay = [605, 219, 176, 210]
pm, pc, pn, pp = plt.bar(ind-0.2, processDelay,width=0.4)
# pm.set_facecolor('r')
# pc.set_facecolor('g')
# pn.set_facecolor('b')
ax.set_xticks(ind)
ax.set_xticklabels(['S. 1', 'S. 2', 'S. 3','S. 4'],fontsize = 48)
# ax.set_ylim([0, 100])
ax.set_ylabel('Processing (s)',fontsize = 48)
ax.set_title('Latency',fontsize = 48)

ax2 = ax.twinx()
ax2.set_ylabel('Network (ms)',fontsize = 48)
processDelay = [21, 5.9, 5.6, 19]
ax2.bar(ind+0.2, processDelay, color='r',width=0.4)

ax.tick_params(axis='both', which='major', labelsize=30)
ax.tick_params(axis='both', which='minor', labelsize=20)

ax2.tick_params(axis='both', which='major', labelsize=30)
ax2.tick_params(axis='both', which='minor', labelsize=20)

plt.grid()
plt.show(block=True)

#
# start = time.time()
# for i in range(200):  # run for a little while
#     m, c, n = get_stats(i / 10.0)
#
#     # update the animated artists
#     pm.set_height(m)
#     pc.set_height(c)
#     pn.set_height(n)
#
#     # ask the canvas to re-draw itself the next time it
#     # has a chance.
#     # For most of the GUI backends this adds an event to the queue
#     # of the GUI frameworks event loop.
#     fig.canvas.draw_idle()
#     try:
#         # make sure that the GUI framework has a chance to run its event loop
#         # and clear any GUI events.  This needs to be in a try/except block
#         # because the default implementation of this method is to raise
#         # NotImplementedError
#         fig.canvas.flush_events()
#     except NotImplementedError:
#         pass
#
# stop = time.time()
# print("{fps:.1f} frames per second".format(fps=200 / (stop - start)))