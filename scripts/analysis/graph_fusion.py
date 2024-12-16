#!/usr/bin/env python3

import os
import tarfile
import networkx as nx
import pydot  # For parsing .dot files

# Input folder and output folder
input_folder = "."
output_folder = "ipsm"
os.makedirs(output_folder, exist_ok=True)

def extract_and_merge_graphs(set_label):
    """
    Extracts and merges all ipsm.dot graphs from the .tar.gz files in the specified set.
    """
    graph = nx.DiGraph()  # Assuming directed graph; use nx.Graph() for undirected
    
    for i in range(1, 9):  # Loop through files named out-lightftp-{set_label}_{index}.tar.gz
        tar_filename = f"out-lightftp-{set_label}_{i}.tar.gz"
        tar_path = os.path.join(input_folder, tar_filename)
        
        # Check if the file exists
        if not os.path.isfile(tar_path):
            print(f"File {tar_path} not found!")
            continue
        
        # Extract the .dot file
        with tarfile.open(tar_path, "r:gz") as tar:
            ipsm_file = [name for name in tar.getnames() if name.endswith("ipsm.dot")]
            if not ipsm_file:
                print(f"No ipsm.dot found in {tar_path}")
                continue
            
            ipsm_file = ipsm_file[0]  # There should be only one
            with tar.extractfile(ipsm_file) as file:
                if file:
                    dot_data = file.read().decode('utf-8')  # Decode bytes to string
                    
                    # Parse the dot data with pydot
                    pydot_graphs = pydot.graph_from_dot_data(dot_data)
                    if pydot_graphs:  # Ensure at least one graph is parsed
                        temp_graph = nx.drawing.nx_pydot.from_pydot(pydot_graphs[0])  # Convert to networkx graph
                        
                        # Validate the temp_graph
                        if isinstance(temp_graph, (nx.Graph, nx.DiGraph)):
                            graph = nx.compose(graph, temp_graph)  # Merge graphs
                        else:
                            print(f"Invalid graph object in {tar_path}")
    
    # Write the combined graph to a new .dot file
    output_path = os.path.join(output_folder, f"ipsm-{set_label}.dot")
    nx.drawing.nx_pydot.write_dot(graph, output_path)
    print(f"Combined graph for set {set_label} written to {output_path}")

# Process both sets (replace 'set1' and 'set2' with your actual set labels)
set_labels = ["aflnet", "aflnet-tuples"]  # Replace with your actual set labels
for set_label in set_labels:
    extract_and_merge_graphs(set_label)