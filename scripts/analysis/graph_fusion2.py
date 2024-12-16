#!/usr/bin/env python3

import os
import tarfile
import tempfile
import networkx as nx
from networkx.drawing.nx_agraph import read_dot, write_dot
from collections import defaultdict

def extract_dot_files_from_tar(tar_path, extract_dir):
    """
    Extracts all .dot files from a given .tar.gz file into a temporary directory.
    """
    dot_files = []
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith(".dot"):
                    tar.extract(member, extract_dir)
                    dot_files.append(os.path.join(extract_dir, member.name))
    except Exception as e:
        print(f"Error extracting {tar_path}: {e}")
    return dot_files

def merge_dot_graphs(dot_files, output_file):
    """
    Merges multiple .dot files into a single graph and saves the result.
    """
    master_graph = nx.MultiDiGraph()
    
    for dot_file in dot_files:
        try:
            temp_graph = read_dot(dot_file)
            
            for node, data in temp_graph.nodes(data=True):
                if not master_graph.has_node(node):
                    master_graph.add_node(node, **data)
                else:
                    master_graph.nodes[node].update(data)
            
            for u, v, key, data in temp_graph.edges(data=True, keys=True):
                master_graph.add_edge(u, v, key=key, **data)
        
        except Exception as e:
            print(f"Error processing {dot_file}: {e}")
    
    write_dot(master_graph, output_file)
    print(f"Merged graph saved to {output_file}")

def process_tar_files_by_set(tar_files, output_dir):
    """
    Groups .tar.gz files by set name, extracts .dot files, merges them, and saves the merged graphs.
    """
    # Group tar files by set name (e.g., "lightftp-aflnet" or "lightftp-someother")
    grouped_files = defaultdict(list)
    for tar_file in tar_files:
        # Extract set name from filename (e.g., "out-lightftp-aflnet_1.tar.gz" -> "aflnet")
        base_name = os.path.basename(tar_file)
        set_name = base_name.split("-")[2].split("_")[0]
        grouped_files[set_name].append(tar_file)

    with tempfile.TemporaryDirectory() as temp_dir:
        for set_name, files in grouped_files.items():
            print(f"Processing set: {set_name}")
            all_dot_files = []

            for tar_file in files:
                print(f"  Extracting {tar_file}...")
                extracted_dot_files = extract_dot_files_from_tar(tar_file, temp_dir)
                all_dot_files.extend(extracted_dot_files)

            # Merge and save the merged graph for this set
            output_file = os.path.join(output_dir, f"merged_graph_{set_name}.dot")
            merge_dot_graphs(all_dot_files, output_file)

if __name__ == "__main__":
    # Directory containing all .tar.gz files
    tar_dir = "."
    output_dir = "./merged_graphs"
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Collect all .tar.gz files
    tar_files = [os.path.join(tar_dir, f) for f in os.listdir(tar_dir) if f.endswith(".tar.gz")]
    
    # Process and merge graphs by set name
    process_tar_files_by_set(tar_files, output_dir)
