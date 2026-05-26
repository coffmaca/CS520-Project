import networkx as nx
from load_graph import load_graph


def compute_reachability(graph):
    nodes = graph.nodes.items()

    reach = {}
    for node in nodes:
        reach[node[0]] = {}
        reach[node[0]]["in"] = nx.ancestors(G=graph, source=node[0])
        reach[node[0]]["out"] = nx.descendants(G=graph, source=node[0])

    return reach

if __name__ == "__main__":
    graph_path = "graph.pkl"

    G = load_graph(graph_path)

    reach = compute_reachability(G)