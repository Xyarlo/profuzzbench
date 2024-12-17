#!/usr/bin/env python3

import os
import tarfile
import pydot
from pathlib import Path

def extract_tar_to_unique_dir(tar_path, extract_to_base):
    """
    Extract a .tar.gz file into a unique subdirectory of extract_to_base.
    """
    unique_dir = Path(extract_to_base) / tar_path.stem  # Unique directory name
    unique_dir.mkdir(parents=True, exist_ok=True)
    
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(unique_dir)  # Extract all files into the unique directory
    return unique_dir


def find_ipsm_dot_files(extracted_dir):
    """
    Find all `ipsm.dot` files in the extracted directory.
    """
    return list(Path(extracted_dir).rglob("ipsm.dot"))


def merge_dot_graphs(dot_files, output_file):
    """
    Merge multiple .dot files into a single graph and save the result.
    """
    master_graph = pydot.Dot(graph_type='digraph', strict=True)
    added_nodes = set()
    added_edges = set()

    print(f"Merging {len(dot_files)} files into {output_file}...")

    for dot_file in dot_files:
        try:
            graphs = pydot.graph_from_dot_file(str(dot_file))
            if graphs:
                for graph in graphs:
                    for node in graph.get_nodes():
                        if node.get_name() not in added_nodes:
                            master_graph.add_node(node)
                            added_nodes.add(node.get_name())
                    for edge in graph.get_edges():
                        edge_tuple = (edge.get_source(), edge.get_destination())
                        if edge_tuple not in added_edges:
                            master_graph.add_edge(edge)
                            added_edges.add(edge_tuple)
        except Exception as e:
            print(f"Error processing {dot_file}: {e}")

    if master_graph.get_nodes():
        master_graph.write_raw(output_file)
        print(f"Merged graph saved to {output_file}")
    else:
        print(f"No valid graphs to merge for {output_file}")


def process_tar_files_by_set(tar_files, output_dir):
    """
    Process tar.gz files grouped by set names and merge their graphs.
    """
    grouped_files = {}
    for tar_file in tar_files:
        set_name = tar_file.stem.split("-")[-1].split("_")[0]  # Extract the set name
        grouped_files.setdefault(set_name, []).append(tar_file)

    for set_name, files in grouped_files.items():
        print(f"\nProcessing set: {set_name}")
        extracted_dot_files = []

        # Extract each .tar.gz into a unique directory
        for tar_file in files:
            extracted_dir = extract_tar_to_unique_dir(tar_file, output_dir)
            ipsm_files = find_ipsm_dot_files(extracted_dir)
            if ipsm_files:
                extracted_dot_files.extend(ipsm_files)
                print(f"Found {len(ipsm_files)} ipsm.dot file(s) in {tar_file}")
            else:
                print(f"No 'ipsm.dot' found in {tar_file}")

        # Merge all the .dot files for this set
        if extracted_dot_files:
            merged_file_path = Path(output_dir) / f"merged_graph_{set_name}.dot"
            merge_dot_graphs(extracted_dot_files, merged_file_path)
        else:
            print(f"No .dot files to merge for set: {set_name}")


# Example Usage
input_tar_dir = "."  # Directory containing .tar.gz files
output_dir = "./merged_graphs"

Path(output_dir).mkdir(parents=True, exist_ok=True)
tar_files = list(Path(input_tar_dir).glob("*.tar.gz"))
process_tar_files_by_set(tar_files, output_dir)
