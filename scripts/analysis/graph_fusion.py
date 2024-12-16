#!/usr/bin/env python3

import os
import tarfile
import networkx as nx
import pydot

input_folder = "."
output_folder = "ipsm"
os.makedirs(output_folder, exist_ok=True)

def extract_and_merge_graphs(set_label):
    """
    Extracts and merges all ipsm.dot graphs from the .tar.gz files in the specified set.
    """
    graph = nx.DiGraph()  # Assuming directed graph; use nx.Graph() for undirected
    
    for i in range(1, 9):
        tar_filename = f"out-lightftp-{set_label}_{i}.tar.gz"
        tar_path = os.path.join(input_folder, tar_filename)
        
        if not os.path.isfile(tar_path):
            print(f"File {tar_path} not found!")
            continue
        
        with tarfile.open(tar_path, "r:gz") as tar:
            ipsm_file = [name for name in tar.getnames() if name.endswith("ipsm.dot")]
            if not ipsm_file:
                print(f"No ipsm.dot found in {tar_path}")
                continue
            
            ipsm_file = ipsm_file[0]
            with tar.extractfile(ipsm_file) as file:
                if file:
                    dot_data = file.read().decode('utf-8')
                    
                    pydot_graphs = pydot.graph_from_dot_data(dot_data)
                    if pydot_graphs:
                        temp_graph = nx.drawing.nx_pydot.from_pydot(pydot_graphs[0])
                        
                        # Debugging and validation
                        print(f"temp_graph type: {type(temp_graph)}")
                        print(f"temp_graph nodes: {temp_graph.nodes(data=True)}")
                        print(f"temp_graph edges: {temp_graph.edges(data=True)}")
                        
                        if isinstance(temp_graph, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)):
                            print(f"Merging graph from {tar_path}...")
                            graph = nx.compose(graph, temp_graph)
                        else:
                            print(f"Invalid graph object from {tar_path}. Type: {type(temp_graph)}")
                    else:
                        print(f"Failed to parse .dot data from {tar_path}")
    
    output_path = os.path.join(output_folder, f"ipsm-{set_label}.dot")
    nx.drawing.nx_pydot.write_dot(graph, output_path)
    print(f"Combined graph for set {set_label} written to {output_path}")

set_labels = ["aflnet", "aflnet-tuples"]  # Replace with your actual set labels
for set_label in set_labels:
    extract_and_merge_graphs(set_label)
