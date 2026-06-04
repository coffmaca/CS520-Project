import pickle
import networkx as nx

# Use networkx strongly_connected_components() function to separate graph
with open("data/graph.pkl", "rb") as f:
    G = pickle.load(f)

    SCCs = list(nx.strongly_connected_components(G))

# Print notable details
print(f"Number of SCCs: {len(SCCs)}")
print(f"Largest SCC size: {max(len(SCC) for SCC in SCCs)}")

# Find SCCs with multiple vertices
counter = 0
for SCC in SCCs:
    if len(SCC) != 1:
        counter += 1
        print(f"Size of SCC {counter}: {len(SCC)}")

print(f"Number of SCCs with multiple vertices", counter)
