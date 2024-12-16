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

                    # Handle subgraphs explicitly
                    for subgraph in graph.get_subgraphs():
                        for node in subgraph.get_nodes():
                            node_id = normalize_identifier(node.get_name())
                            if node_id not in added_nodes:
                                master_graph.add_node(node)
                                added_nodes.add(node_id)
                                print(f"Added node (subgraph): {node_id}")
                            else:
                                print(f"Skipped duplicate node (subgraph): {node_id}")

                        for edge in subgraph.get_edges():
                            edge_source = normalize_identifier(edge.get_source())
                            edge_dest = normalize_identifier(edge.get_destination())
                            edge_tuple = (edge_source, edge_dest)
                            if edge_tuple not in added_edges:
                                master_graph.add_edge(edge)
                                added_edges.add(edge_tuple)
                                print(f"Added edge (subgraph): {edge_source} -> {edge_dest}")
                            else:
                                print(f"Skipped duplicate edge (subgraph): {edge_source} -> {edge_dest}")

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
