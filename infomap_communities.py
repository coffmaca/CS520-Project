import os
import pandas as pd
import networkx as nx
from infomap import Infomap
from load_graph import load_graph

# File paths
GRAPH_PATH = "data/graph.pkl"
COMMUNITY_PATH = "data/infomap_communities.pkl"
SUMMARY_PATH = "data/infomap_summary.pkl"

# Infomap settings
NUM_TRIALS = 50  # How many times Infomap restarts from scratch
MIN_EDGE_WEIGHT = 3.0  # Filter out edges with weight below this threshold to reduce noise
FLOW_MODEL = "undirdir"  # "directed" | "undirdir" | "outdirdir" | "rawdir"
MARKOV_TIME = 0.75  # Markov time controls the resolution of communities: <1 favors smaller communities, >1 favors larger ones
TOP_K = 5  # How many top members to show per community in the summary output


def filter_graph(G, min_weight):
    # Keep only stronger connections
    weak_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("Weight", 0) < min_weight]

    G_f = G.copy()
    G_f.remove_edges_from(weak_edges)

    # Drop nodes that no longer connect to anyone
    isolates = list(nx.isolates(G_f))
    G_f.remove_nodes_from(isolates)

    print("  After filtering (weight < " + str(min_weight) + "):")
    print("    Removed " + str(len(weak_edges)) + " edges, " + str(len(isolates)) + " isolates")
    print("    Remaining: " + str(G_f.number_of_nodes()) + " nodes | " + str(G_f.number_of_edges()) + " edges")

    return G_f


def _build_infomap(G, num_trials, flow_model, markov_time):
    # Build Infomap with the chosen settings
    flags = "--num-trials " + str(num_trials) + " " "--directed " "--flow-model " + flow_model + " " "--markov-time " + str(markov_time) + " " "--silent"
    im = Infomap(flags)

    # Infomap uses integer ids, so map emails to numbers
    node_to_id = {node: idx for idx, node in enumerate(G.nodes())}
    id_to_node = {idx: node for node, idx in node_to_id.items()}

    for u, v, data in G.edges(data=True):
        weight = data.get("Weight", 1.0)
        im.add_link(node_to_id[u], node_to_id[v], weight)

    im.run()
    return im, node_to_id, id_to_node


def run_infomap(
    G,
    num_trials=NUM_TRIALS,
    min_edge_weight=MIN_EDGE_WEIGHT,
    flow_model=FLOW_MODEL,
    markov_time=MARKOV_TIME,
):
    G_filtered = filter_graph(G, min_edge_weight)
    im, _, id_to_node = _build_infomap(G_filtered, num_trials, flow_model, markov_time)

    rows = []
    for node in im.nodes:
        rows.append(
            {
                "Node": id_to_node[node.node_id],
                "Module": node.module_id,
                "Submodule": node.path,
                "Flow": node.flow,
            }
        )

    df = pd.DataFrame(rows)
    df.sort_values(["Module", "Flow"], ascending=[True, False], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def get_community_summary(community_df, top_k=TOP_K):
    rows = []

    for module_id, grp in community_df.groupby("Module"):
        grp_sorted = grp.sort_values("Flow", ascending=False)
        rows.append(
            {
                "Module": module_id,
                "Size": len(grp),
                "Total_Flow": round(grp["Flow"].sum(), 6),
                "Top_K_Nodes": grp_sorted["Node"].head(top_k).tolist(),
            }
        )

    summary = pd.DataFrame(rows)
    summary.sort_values("Total_Flow", ascending=False, inplace=True)
    summary.reset_index(drop=True, inplace=True)
    return summary


def print_diagnostics(summary_df):
    largest = summary_df["Size"].max()

    #  Count modules with >100 members
    n_giant = len(summary_df[summary_df["Size"] > 100])

    # Count modules in the "working group" size range (5–500 members)
    n_medium = len(summary_df[(summary_df["Size"] >= 5) & (summary_df["Size"] <= 500)])

    # Check for giant-module problem: if there is only 1 module and it is very large -> red flag
    if n_giant == 1 and largest > 5000:
        giant_flag = "  WARNING: giant-module problem"
    else:
        giant_flag = "  OK"

    print("")
    print("-- Diagnostics -------------------------------------------")
    print("  Total modules            : " + str(len(summary_df)))
    print("  Largest module size      : " + str(largest))
    print("  Modules with >100 members: " + str(n_giant) + giant_flag)
    print("  Working-group modules    : " + str(n_medium) + "  (5-500 members)")
    print("----------------------------------------------------------")


if __name__ == "__main__":
    print("Loading graph ...")
    G = load_graph(GRAPH_PATH)
    print("  Nodes: " + str(G.number_of_nodes()) + "  |  Edges: " + str(G.number_of_edges()))

    print("")
    print("Running Infomap ...")
    print("  num_trials=" + str(NUM_TRIALS) + ", min_edge_weight=" + str(MIN_EDGE_WEIGHT) + ", flow_model=" + FLOW_MODEL + ", markov_time=" + str(MARKOV_TIME))

    community_df = run_infomap(
        G,
        num_trials=NUM_TRIALS,
        min_edge_weight=MIN_EDGE_WEIGHT,
        flow_model=FLOW_MODEL,
        markov_time=MARKOV_TIME,
    )

    summary_df = get_community_summary(community_df, top_k=TOP_K)

    print("")
    print("Found " + str(community_df["Module"].nunique()) + " top-level modules")
    print("")
    print("Top 15 modules by total flow:")
    print(summary_df.head(15).to_string(index=False))

    print_diagnostics(summary_df)

    os.makedirs("data", exist_ok=True)
    community_df.to_pickle(COMMUNITY_PATH)
    summary_df.to_pickle(SUMMARY_PATH)

    print("")
    print("Saved per-node assignments -> " + COMMUNITY_PATH)
    print("Saved module summary       -> " + SUMMARY_PATH)
