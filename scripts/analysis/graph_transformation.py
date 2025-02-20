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
    with open(input_file, 'r') as f:
        content = f.read()

    # Find all node IDs (assuming they are integers in the graph)
    node_pattern = re.compile(r'\b(\d+)\b')
    node_declaration_pattern = re.compile(r'^(\d+) \[label=".*?", weight=(\d+)\];', re.MULTILINE)
    edge_pattern = re.compile(r'^(\d+) -> (\d+) \[label=(\d+), weight=(\d+)\];', re.MULTILINE)

    unique_nodes = set(map(int, node_pattern.findall(content)))

    # Create a mapping of original node IDs to new unique IDs with tuple labels
    id_map = {}
    for node in unique_nodes:
        tuple_label = convert_node_id_to_tuple(node)
        new_id = f"node{len(id_map) + 1}"
        id_map[node] = (new_id, tuple_label)

    # Replace node declarations while keeping weights
    def replace_node_declaration(match):
        original_id = int(match.group(1))
        weight = match.group(2)
        new_id, tuple_label = id_map[original_id]
        return f'    {new_id} [label="<{tuple_label[0]},{tuple_label[1]}>", weight={weight}];'
    
    content = node_declaration_pattern.sub(replace_node_declaration, content)

    # Replace edges while keeping weights
    def replace_edge(match):
        original_source = int(match.group(1))
        original_target = int(match.group(2))
        label = match.group(3)
        weight = match.group(4)
        new_source, _ = id_map[original_source]
        new_target, _ = id_map[original_target]
        return f'    {new_source} -> {new_target} [label={label}, weight={weight}];'
    
    content = edge_pattern.sub(replace_edge, content)

    # Write to the output file
    with open(output_file, 'w') as f:
        f.write(content)


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
