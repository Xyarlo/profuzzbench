#!/usr/bin/env python

import re
import os

def convert_node_id_to_tuple(node_id):
    """Convert a 32-bit unsigned integer into a tuple of two 16-bit unsigned integers."""
    high = (node_id >> 16) & 0xFFFF
    low = node_id & 0xFFFF
    return high, low

def transform_dot_file(input_file, output_file):
    """Transform a .dot file, replacing node IDs with unique identifiers and adding tuple labels."""
    with open(input_file, 'r') as f:
        content = f.read()

    # Find all node IDs (assuming they are integers in the graph)
    node_pattern = re.compile(r'\b(\d+)\b')
    unique_nodes = set(map(int, node_pattern.findall(content)))

    # Create a mapping of original node IDs to new unique IDs with tuple labels
    id_map = {}
    for node in unique_nodes:
        tuple_label = convert_node_id_to_tuple(node)
        new_id = f"node{len(id_map) + 1}"
        id_map[node] = (new_id, tuple_label)

    # Replace node IDs in the content
    def replace_node_id(match):
        original_id = int(match.group(1))
        new_id, _ = id_map[original_id]
        return new_id

    transformed_content = node_pattern.sub(replace_node_id, content)

    # Add labels for nodes
    labels = []
    for original_id, (new_id, tuple_label) in id_map.items():
        labels.append(f'    {new_id} [label="<{tuple_label[0]},{tuple_label[1]}>"];')

    # Insert labels into the graph definition
    transformed_content = re.sub(r'(\{)', r'\1\n' + "\n".join(labels), transformed_content, count=1)

    # Write to the output file
    with open(output_file, 'w') as f:
        f.write(transformed_content)


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
