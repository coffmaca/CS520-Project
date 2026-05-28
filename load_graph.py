import networkx as nx
import pickle


def load_graph(path):
    with open(path, 'rb') as f:
        G = pickle.load(f)

    return G


if __name__ == "__main__":
    graph_path = "graph_filtered.pkl"  # Update as necessary
    load_graph(graph_path)