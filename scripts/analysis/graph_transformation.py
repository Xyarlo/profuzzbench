#!/usr/bin/env python

import re
import os

def convert_node_id_to_tuple(node_id):
    """Convert a 32-bit unsigned integer into a tuple of two 16-bit unsigned integers."""
    high = (node_id >> 16) & 0xFFFF
    low = node_id & 0xFFFF
    return high, low

def transform_dot_file(input_file, output_file):
    """Transform a .dot file, replacing node IDs with unique identifiers and adding tuple labels while keeping weights."""
    if not os.path.exists(input_file):
        print(f"Skipping {input_file}: File not found.")
        return
    
    with open(input_file, 'r') as f:
        content = f.read()

    # Find all node IDs (assuming they are integers in the graph)
    node_declaration_pattern = re.compile(r'^(\d+) \[label=".*?", weight=(\d+)\];', re.MULTILINE)
    edge_pattern = re.compile(r'^(\d+) -> (\d+) \[label=(\d+), weight=(\d+)\];', re.MULTILINE)

    # Extract unique node IDs from the node declarations and sort them numerically
    unique_nodes = sorted(set(int(match.group(1)) for match in node_declaration_pattern.finditer(content)))
    
    # Assign sequential names strictly in increasing order
    id_map = {node: (f"node{index + 1}", convert_node_id_to_tuple(node)) for index, node in enumerate(unique_nodes)}
    
    # Ensure nodes are written first in the correct order
    transformed_lines = ["strict digraph G {\n"]
    transformed_lines.append("node [label=\"node (8)\", weight=8];\n")
    transformed_lines.append("edge [label=\"edge (8)\", weight=8];\n")

    # Replace node declarations while keeping weights
    for node in unique_nodes:
        new_id, tuple_label = id_map[node]
        weight = next(match.group(2) for match in node_declaration_pattern.finditer(content) if int(match.group(1)) == node)
        transformed_lines.append(f'    {new_id} [label="<{tuple_label[0]},{tuple_label[1]}>", weight={weight}];\n')

    # Replace edges while keeping weights
    for match in edge_pattern.finditer(content):
        original_source = int(match.group(1))
        original_target = int(match.group(2))
        label = match.group(3)
        weight = match.group(4)
        new_source, _ = id_map[original_source]
        new_target, _ = id_map[original_target]
        transformed_lines.append(f'    {new_source} -> {new_target} [label={label}, weight={weight}];\n')
    
    transformed_lines.append("}\n")
    
    # Write to the output file
    with open(output_file, 'w') as f:
        f.writelines(transformed_lines)


def main():
    # List of files to transform
    files_to_transform = [
        "merged_graph_delayed.dot",
        "merged_graph_tuples.dot",
    ]

    # Process each file
    for input_file in files_to_transform:
        output_file = os.path.splitext(input_file)[0] + "_transformed.dot"
        print(f"Transforming {input_file} -> {output_file}")
        transform_dot_file(input_file, output_file)

if __name__ == "__main__":
    main()
