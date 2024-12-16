#!/usr/bin/env python3

import os
import tarfile
import pydot
from pathlib import Path


def extract_tar_to_unique_dir(tar_path, extract_to_base):
    """
    Extract a .tar.gz file to a unique directory inside extract_to_base.
    """
    unique_dir = Path(extract_to_base) / tar_path.stem  # Unique dir based on the tar.gz name
    unique_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(unique_dir)
    
    return unique_dir


def merge_dot_graphs(dot_files, output_file):
    """
    Merges multiple .dot files into a single graph and saves the result.
    """
    master_graph = pydot.Dot(graph_type='digraph', strict=True)  # Strict to prevent duplicates
    added_nodes = set()
    added_edges = set()

    def normalize_identifier(identifier):
        """Normalize node or edge identifiers for consistent comparison."""
        return identifier.strip('"').strip()

    print(f"Merging {len(dot_files)} files into {output_file}...")

    for dot_file in dot_files:
        try:
            graphs = pydot.graph_from_dot_file(dot_file)
            if graphs:
                for graph in graphs:
                    print(f"Processing {dot_file}...")

                    # Add nodes
                    for node in graph.get_nodes():
                        node_id = normalize_identifier(node.get_name())
                        if node_id not in added_nodes:
                            master_graph.add_node(node)
                            added_nodes.add(node_id)
                            print(f"Added node: {node_id}")
                        else:
                            print(f"Skipped duplicate node: {node_id}")

                    # Add edges
                    for edge in graph.get_edges():
                        edge_source = normalize_identifier(edge.get_source())
                        edge_dest = normalize_identifier(edge.get_destination())
                        edge_tuple = (edge_source, edge_dest)
                        if edge_tuple not in added_edges:
                            master_graph.add_edge(edge)
                            added_edges.add(edge_tuple)
                            print(f"Added edge: {edge_source} -> {edge_dest}")
                        else:
                            print(f"Skipped duplicate edge: {edge_source} -> {edge_dest}")

        except Exception as e:
            print(f"Error processing {dot_file}: {e}")

    print(f"Total nodes in merged graph: {len(added_nodes)}")
    print(f"Total edges in merged graph: {len(added_edges)}")

    if master_graph.get_nodes():
        master_graph.write_raw(output_file)
        print(f"Merged graph saved to {output_file}")
    else:
        print(f"No valid graphs to merge for {output_file}")


def process_tar_files_by_set(tar_files, output_dir):
    """
    Process tar.gz files by set names and merge graphs.
    """
    grouped_files = {}
    for tar_file in tar_files:
        set_name = tar_file.stem.split("-")[-1].split("_")[0]  # Extract the set name
        grouped_files.setdefault(set_name, []).append(tar_file)

    for set_name, files in grouped_files.items():
        print(f"Processing set: {set_name}")

        extracted_dot_files = []
        for tar_file in files:
            extracted_dir = extract_tar_to_unique_dir(tar_file, output_dir)
            extracted_dot_file = extracted_dir / "ipsm.dot"
            if extracted_dot_file.exists():
                extracted_dot_files.append(extracted_dot_file)
            else:
                print(f"No 'ipsm.dot' found in {tar_file}.")

        # Merge the .dot files for the current set
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
