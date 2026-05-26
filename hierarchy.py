import networkx as nx
import pandas as pd
from load_graph import load_graph


def compute_reachability(graph):
    nodes = graph.nodes.items()

    reach = []
    for node in nodes:
        node_data = [node[0]]
        node_data.append(len(nx.ancestors(G=graph, source=node[0])))
        node_data.append(len(nx.descendants(G=graph, source=node[0])))
        reach.append(node_data)

    reach_df = pd.DataFrame(reach, columns=["Node", "Reachability (In)", "Reachability (Out)"])

    return reach_df

if __name__ == "__main__":
    graph_path = "graph.pkl"

    G = load_graph(graph_path)

    reach = compute_reachability(G)
    pd.to_pickle(reach, "reach.pkl")