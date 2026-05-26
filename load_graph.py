import networkx as nx
import pickle


GRAPH_PATH = "graph.pkl"  # Update as necessary


def main():
    with open(GRAPH_PATH, 'rb') as f:
        G = pickle.load(f)

    print("")


if __name__ == "__main__":
    main()