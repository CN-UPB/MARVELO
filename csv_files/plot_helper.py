import matplotlib.pyplot as plt
import numpy as np
# Create bars
barWidth = 0.25
bars1 = [3, 3, 1]
bars2 = [4, 2, 3]
bars3 = [4, 6, 7,]
bars4 = bars1 + bars2 + bars3
barst = [bars1 , bars2 , bars3]

# The X position of bars
r1 = list(range(0,3))
r2 = [2, 6, 10]
r3 = [3, 4, 7, 8, 11, 12]
# r4 = r1 + r2 + r3
rt =np.array(r1)

def bar_plot(barst,scenarios,apps,barWidth=0.2):
    rt= range(len(apps))
    for i in range(len(barst)):
        plt.bar(np.array(rt)+i*barWidth, barst[i], width=barWidth, label=scenarios[i])
    plt.legend()
    plt.xticks([r  for r in range(len(rt))],
               [apps[i] for i in range(len(rt))], rotation=90)
    plt.subplots_adjust(bottom=0.2, top=0.98)



for i in range(len(barst)):
    plt.bar(rt+i*barWidth, barst[i], width=barWidth, label=f"scenario{i}")
plt.legend()
plt.xticks([r  for r in range(len(rt))],
           [f"app{i}" for i in range(len(rt))], rotation=90)
plt.subplots_adjust(bottom=0.2, top=0.98)

# Text below each barplot with a rotation at 90°
plt.xticks([r  for r in range(len(rt))],
           [f"app{i}" for i in range(len(rt))], rotation=90)

# Create labels
# label = ['n = 6', 'n = 25', 'n = 13', 'n = 36', 'n = 30', 'n = 11', 'n = 16', 'n = 37', 'n = 14', 'n = 4', 'n = 31',
#          'n = 34']

# Text on the top of each barplot
# for i in range(len(r4)):
#     plt.text(x=r4[i] - 0.5, y=bars4[i] + 0.1, s=label[i], size=6)

# Adjust the margins
plt.subplots_adjust(bottom=0.2, top=0.98)

# Show graphic
plt.show()
