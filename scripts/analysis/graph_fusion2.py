#!/usr/bin/env python3

import os
import tarfile
import tempfile
import pydot
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
    master_graph = None

    for dot_file in dot_files:
        try:
            graphs = pydot.graph_from_dot_file(dot_file)
            if graphs:
                for graph in graphs:
                    if master_graph is None:
                        master_graph = graph
                    else:
                        for node in graph.get_nodes():
                            if node not in master_graph.get_nodes():
                                master_graph.add_node(node)
                        for edge in graph.get_edges():
                            master_graph.add_edge(edge)
        except Exception as e:
            print(f"Error processing {dot_file}: {e}")
    
    if master_graph:
        master_graph.write_raw(output_file)
        print(f"Merged graph saved to {output_file}")
    else:
        print(f"No valid graphs to merge for {output_file}")

def process_tar_files_by_set(tar_files, output_dir):
    """
    Groups .tar.gz files by exact set name, extracts .dot files, merges them, and saves the merged graphs.
    """
    grouped_files = {"aflnet": [], "aflnet-tuples": []}

    # Assign files to their respective sets
    for tar_file in tar_files:
        if "-aflnet_" in tar_file:
            grouped_files["aflnet"].append(tar_file)
        elif "-aflnet-tuples_" in tar_file:
            grouped_files["aflnet-tuples"].append(tar_file)

    with tempfile.TemporaryDirectory() as temp_dir:
        for set_name, files in grouped_files.items():
            if not files:
                print(f"No files found for set: {set_name}")
                continue

            print(f"Processing set: {set_name}")
            all_dot_files = []

            for tar_file in files:
                print(f"  Extracting {tar_file}...")
                extracted_dot_files = extract_dot_files_from_tar(tar_file, temp_dir)
                all_dot_files.extend(extracted_dot_files)

            output_file = os.path.join(output_dir, f"merged_graph_{set_name}.dot")
            merge_dot_graphs(all_dot_files, output_file)

if __name__ == "__main__":
    tar_dir = "."
    output_dir = "./merged_graphs"
    os.makedirs(output_dir, exist_ok=True)
    tar_files = [os.path.join(tar_dir, f) for f in os.listdir(tar_dir) if f.endswith(".tar.gz")]
    process_tar_files_by_set(tar_files, output_dir)
