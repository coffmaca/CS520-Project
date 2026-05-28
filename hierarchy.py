import networkx as nx
import numpy as np
import pandas as pd
from load_graph import load_graph
import time


def compute_degree_metrics(G):
    degree = dict(G.degree())
    in_degree = dict(G.in_degree())
    out_degree = dict(G.out_degree())

    degree_df = pd.DataFrame({
        'degree': degree,
        'in_degree': in_degree,
        'out_degree': out_degree
    })

    degree_df.reset_index(inplace=True)
    degree_df.rename(columns={'index': 'Node'}, inplace=True)

    valid_mask = (
            degree_df['in_degree'].notna() &
            (degree_df['in_degree'] != 0) &
            degree_df['out_degree'].notna() &
            (degree_df['out_degree'] != 0)
    )

    degree_df['Ratio (In/Out)'] = np.where(
        valid_mask,
        degree_df['in_degree'].astype(float) / degree_df['out_degree'].astype(float),
        0.0
    )

    degree_df = degree_df[degree_df['Ratio (In/Out)'] != 0].copy()

    base_cols = ['degree', 'in_degree', 'out_degree', 'Ratio (In/Out)']
    std_dev_cols = []

    for col in base_cols:
        new_col_name = f'{col}_std_dev'
        std_dev_cols.append(new_col_name)

        degree_df[new_col_name] = (degree_df[col] - degree_df[col].mean()) / degree_df[col].std()

    degree_df['Total_std_devs'] = degree_df[std_dev_cols].sum(axis=1)

    return degree_df


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

    apsp_ratio_df = pd.DataFrame({'Node': all_vertices})

    # no_path_mask = apsp_all_df['Length'] == 0

    # apsp_all_df['Length'] = np.where(
    #     no_path_mask,
    #     10,
    #     apsp_all_df['Length']
    # )

    avg_out = apsp_all_df.groupby('Source')['Length'].mean().reset_index()
    avg_out.rename(columns={'Source': 'Node', 'Length': 'Average Shortest Path (Out)'}, inplace=True)
    avg_in = apsp_all_df.groupby('Target')['Length'].mean().reset_index()
    avg_in.rename(columns={'Target': 'Node', 'Length': 'Average Shortest Path (In)'}, inplace=True)

    apsp_ratio_df = apsp_ratio_df.merge(avg_out, on='Node', how='left')
    apsp_ratio_df = apsp_ratio_df.merge(avg_in, on='Node', how='left')

    valid_mask = (
            apsp_ratio_df['Average Shortest Path (In)'].notna() &
            (apsp_ratio_df['Average Shortest Path (In)'] != 0) &
            apsp_ratio_df['Average Shortest Path (Out)'].notna() &
            (apsp_ratio_df['Average Shortest Path (Out)'] != 0)
    )

    # apsp_ratio_df['Average Shortest Path Ratio (In/Out)'] = apsp_ratio_df['Average Shortest Path (In)'] / apsp_ratio_df['Average Shortest Path (Out)']

    apsp_ratio_df['Ratio (Out/In)'] = np.where(
        valid_mask,
        apsp_ratio_df['Average Shortest Path (In)'] / apsp_ratio_df['Average Shortest Path (Out)'],
        0.0
    )

    apsp_ratio_df = apsp_ratio_df[apsp_ratio_df['Ratio (Out/In)'] != 0]

    return apsp_ratio_df


if __name__ == "__main__":
    graph_path = "graph_filtered.pkl"
    degree_df_path = "data/degree_df.pkl" # None # 
    reach_df_path = "data/reach.pkl" # None #
    apsp_stats_df_path = "data/apsp_stats.pkl" # None #
    apsp_all_df_path = "data/apsp_all.pkl" # None #
    apsp_ratio_df_path = "data/apsp_ratio_df.pkl" # None #

    G = load_graph(graph_path)

    # Compute Degree Metrics
    if degree_df_path is None:
        degree_df = compute_degree_metrics(G)
        pd.to_pickle(degree_df, "data/degree_df.pkl")
    else:
        degree_df = pd.read_pickle(degree_df_path)

    # Compute Reachability (To and From)
    if reach_df_path is None:
        reach_df = compute_reachability(G)
        pd.to_pickle(reach_df, "data/reach.pkl")
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