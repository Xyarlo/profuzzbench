#!/usr/bin/env python

import os
import tarfile
import shutil
import pydot
from collections import defaultdict
from pathlib import Path

def extract_tar_to_unique_dir(tar_path, extract_to_base):
    """Extract a .tar.gz file into a unique subdirectory of extract_to_base."""
    unique_dir = Path(extract_to_base) / tar_path.stem
    unique_dir.mkdir(parents=True, exist_ok=True)
    
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(unique_dir)
    return unique_dir


def find_ipsm_dot_files(extracted_dir):
    """Find all `ipsm.dot` files in the extracted directory."""
    return list(Path(extracted_dir).rglob("ipsm.dot"))


def merge_dot_graphs(dot_files, output_file):
    """Merge multiple .dot files into a single graph, adding edge weights based on frequency."""
    master_graph = pydot.Dot(graph_type='digraph', strict=True)
    added_nodes = set()
    edge_counts = defaultdict(int)

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
                        edge_counts[edge_tuple] += 1  # Count occurrences
        except Exception as e:
            print(f"Error processing {dot_file}: {e}")

    # Add edges with weights
    for (src, dst), count in edge_counts.items():
        weighted_edge = pydot.Edge(src, dst, label=str(count), weight=str(count))
        master_graph.add_edge(weighted_edge)

    if master_graph.get_nodes():
        master_graph.write_raw(output_file)
        print(f"Merged graph saved to {output_file}")
    else:
        print(f"No valid graphs to merge for {output_file}")


def process_tar_files_by_set(tar_files, output_dir):
    """Process tar.gz files grouped by set names and merge their graphs."""
    grouped_files = {}
    for tar_file in tar_files:
        set_name = tar_file.stem.split("-")[-1].split("_")[0]  # Extract set name
        grouped_files.setdefault(set_name, []).append(tar_file)

    temp_dirs = []

    for set_name, files in grouped_files.items():
        print(f"\nProcessing set: {set_name}")
        extracted_dot_files = []

        for tar_file in files:
            extracted_dir = extract_tar_to_unique_dir(tar_file, output_dir)
            temp_dirs.append(extracted_dir)
            ipsm_files = find_ipsm_dot_files(extracted_dir)
            if ipsm_files:
                extracted_dot_files.extend(ipsm_files)
                print(f"Found {len(ipsm_files)} ipsm.dot file(s) in {tar_file}")
            else:
                print(f"No 'ipsm.dot' found in {tar_file}")

        if extracted_dot_files:
            merged_file_path = Path(output_dir) / f"merged_graph_{set_name}.dot"
            merge_dot_graphs(extracted_dot_files, merged_file_path)
        else:
            print(f"No .dot files to merge for set: {set_name}")

    # Clean up temporary extraction directories
    for temp_dir in temp_dirs:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error cleaning up {temp_dir}: {e}")



output_dir = "./merged_graphs"

Path(output_dir).mkdir(parents=True, exist_ok=True)
tar_files = list(Path(".").glob("*.tar.gz"))
process_tar_files_by_set(tar_files, output_dir)
