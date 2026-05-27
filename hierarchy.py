import networkx as nx
import numpy as np
import pandas as pd
from load_graph import load_graph
import time


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


def compute_apsp_stats_df(graph):
    apsp = nx.all_pairs_dijkstra_path_length(graph, weight="Weight", backend="cugraph")
    apsp_stats = []
    apsp_all = []
    for item in apsp:
        apsp_item = []
        source = item[0]
        paths = item[1]
        total_path_length = 0
        for dest in paths.keys():
            total_path_length += paths[dest]
            apsp_item.append([source, dest, paths[dest]])
        avg_length = total_path_length / len(paths)
        apsp_stats.append([source, avg_length])
        apsp_all += apsp_item

    apsp_stats_df = pd.DataFrame(apsp_stats, columns=["Source", "Average Length"])
    apsp_all_df = pd.DataFrame(apsp_all, columns=["Source", "Target", "Length"])
    return apsp_stats_df, apsp_all_df


def compute_sp_ratio(apsp_all_df):
    all_vertices = pd.concat([apsp_all_df['Source'], apsp_all_df['Target']]).unique()

    apsp_ratio_df = pd.DataFrame({'Vertex': all_vertices})

    no_path_mask = apsp_all_df['Length'] == 0

    apsp_all_df['Length'] = np.where(
        no_path_mask,
        10,
        apsp_all_df['Length']
    )

    avg_out = apsp_all_df.groupby('Source')['Length'].mean().reset_index()
    avg_out.rename(columns={'Source': 'Vertex', 'Length': 'Average Shortest Path (Out)'}, inplace=True)
    avg_in = apsp_all_df.groupby('Target')['Length'].mean().reset_index()
    avg_in.rename(columns={'Target': 'Vertex', 'Length': 'Average Shortest Path (In)'}, inplace=True)

    apsp_ratio_df = apsp_ratio_df.merge(avg_out, on='Vertex', how='left')
    apsp_ratio_df = apsp_ratio_df.merge(avg_in, on='Vertex', how='left')

    # valid_mask = (
    #         apsp_ratio_df['Average Shortest Path (In)'].notna() &
    #         (apsp_ratio_df['Average Shortest Path (In)'] != 0) &
    #         apsp_ratio_df['Average Shortest Path (Out)'].notna() &
    #         (apsp_ratio_df['Average Shortest Path (Out)'] != 0)
    # )

    apsp_ratio_df['Average Shortest Path Ratio (In/Out)'] = apsp_ratio_df['Average Shortest Path (In)'] / apsp_ratio_df['Average Shortest Path (Out)']

    # apsp_ratio_df['Ratio (Out/In)'] = np.where(
    #     valid_mask,
    #     apsp_ratio_df['Average Shortest Path (In)'] / apsp_ratio_df['Average Shortest Path (Out)'],
    #     0.0
    # )

    return apsp_ratio_df


if __name__ == "__main__":
    graph_path = "data/graph.pkl"
    reach_df_path = "data/reach.pkl"
    apsp_stats_df_path = "data/apsp_stats.pkl"
    apsp_all_df_path = "data/apsp_all.pkl"
    apsp_ratio_df_path = None # "apsp_ratio_df.pkl"

    G = load_graph(graph_path)

    # Compute Reachability (To and From)
    if reach_df_path is None:
        reach_df = compute_reachability(G)
        pd.to_pickle(reach, "data/reach.pkl")
    else:
        reach_df = pd.read_pickle(reach_df_path)

    # Compute All Pairs Shortest Paths
    if apsp_stats_df_path is None or apsp_all_df_path is None:
        apsp_stats_df, apsp_all_df = compute_apsp_stats_df(G)
        pd.to_pickle(apsp_stats_df, "data/apsp_stats.pkl")
        pd.to_pickle(apsp_all_df, "data/apsp_all.pkl")
    else:
        apsp_stats_df = pd.read_pickle(apsp_stats_df_path)
        apsp_all_df = pd.read_pickle(apsp_all_df_path)

    # Compute Shortest Path Ratio (To:From)
    if apsp_ratio_df_path is None:
        apsp_ratio_df = compute_sp_ratio(apsp_all_df)
        pd.to_pickle(apsp_ratio_df, "data/apsp_ratio_df.pkl")
    else:
        apsp_ratio_df = pd.read_pickle(apsp_ratio_df_path)

    print("")