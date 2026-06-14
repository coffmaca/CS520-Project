import igraph as ig
import networkx as nx
import pickle

with open("data/graph.pkl", "rb") as f:
    G = pickle.load(f)
    
    # Convert NetworkX graph to igraph
    G_undirected = G.to_undirected()
    ig_graph = ig.Graph.from_networkx(G_undirected)

    print(ig_graph.vertex_attributes())

    # Run Leiden
    partition = list(
        ig_graph.community_leiden(
            objective_function="modularity",
            weights="Weight",
            resolution=1,
        )
    )

# Sort results by size
partition.sort(key=len, reverse=True)
print(f"Total Leiden Communities: {len(partition)}")
counter = 0
for community in partition:
    counter += 1
    print(f"Size of Community {counter}: {len(community)}")

    # Collect emails
    emails = [
        ig_graph.vs[v]["_nx_name"]
        for v in community
    ]

    # Print
    for email in emails[:10]:
        print(" ", email)
