import subprocess
from fission.core.base import PIPES
# sudo apt install libgraphviz-dev


def generate_detailed_graph(network):
    from graphviz import Digraph
    g = Digraph("Network", engine="fdp")

    for node in network.nodes.values():
        with g.subgraph(name=f'cluster_{node.ip}') as c:
            c.attr(style='filled', color='lightgrey')
            c.node_attr.update(style='filled', color='white')
            for j in node.jobs:
                c.node(f"{j.id}")
            c.attr(label=node.ip)

    for pipe in network.pipes.values():
        g.edge(f"{pipe.source.id}", f"{pipe.destination.id}",
               f"{pipe.id}", style="dashed")
    g.render("temp_network")
    subprocess.Popen(['xdg-open', 'temp_network.pdf'])


def generate_job_graph(network, path):
    from graphviz import Digraph
    print("Generating graph...")
    g = Digraph("Network")  # , node_attr={'shape': 'record', 'height': '.1'})
    g.engine = "circo"
    for job in network.jobs.values():
        g.node(repr(job), fillcolor="deepskyblue1", style="filled")

    for pipe in PIPES.values():
        g.edge(repr(pipe.source), repr(pipe.destination),
               f"{pipe.id}", fontcolor="crimson", style="dashed")
    print(f"Saving to {path}...")
    g.render(path)
    subprocess.Popen(['xdg-open', f'{path}.pdf'])


def show_job_graph(network):
    import matplotlib.pyplot as plt
    import networkx as nx
    print("Generating graph...")
    g = nx.DiGraph()  # , node_attr={'shape': 'record', 'height': '.1'})
    g.engine = "sfdp"
    for job in network.jobs.values():
        g.add_node(repr(job))

    labels = {}
    for pipe in PIPES.values():
        labels[(repr(pipe.source), repr(pipe.destination))] = repr(pipe)
        g.add_edge(repr(pipe.source), repr(pipe.destination))
    print(f"Showing...")
    plt.subplot(111)
    plt.axis('off')
    pos = nx.spring_layout(g)
    nx.draw(g, pos, with_labels=True, node_size=2000)
    nx.draw_networkx_edge_labels(g, pos, edge_labels=labels)
    plt.show()


def get_mermaid(network):
    # TODO mermaid version
    pass
