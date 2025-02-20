#!/usr/bin/env python3

import networkx as nx
import re
import os

def parse_dot_file(file_path):
    graph = nx.DiGraph()
    node_label_pattern = re.compile(r'(\w+) \[label="<(?P<first>\d+),(?P<second>\d+)>".*?\];')
    edge_pattern = re.compile(r'(\w+)\s*->\s*(\w+)\s*\[.*?\];')

    with open(file_path, 'r') as f:
        for line in f:
            match = node_label_pattern.search(line)
            if match:
                node_id = match.group(1)
                first = int(match.group('first'))
                second = int(match.group('second'))
                graph.add_node(node_id, tuple=(first, second))

            edge_match = edge_pattern.search(line)
            if edge_match:
                source = edge_match.group(1)
                target = edge_match.group(2)
                graph.add_edge(source, target)

    return graph

def group_nodes_by_second(graph):
    groups = {}
    for node, data in graph.nodes(data=True):
        _, second = data['tuple']
        groups.setdefault(second, []).append(node)
    return groups

def count_reaching_nodes(graph, source_group, target_group):
    count = 0
    for source in source_group:
        if any(graph.has_edge(source, target) for target in target_group):
            count += 1
    return count

def find_non_reaching_nodes(graph, source_group, target_group):
    non_reaching_nodes = []
    for source in source_group:
        if not any(graph.has_edge(source, target) for target in target_group):
            non_reaching_nodes.append(source)
    return non_reaching_nodes

def analyze_graph(file_path):
    graph = parse_dot_file(file_path)
    groups = group_nodes_by_second(graph)
    
    folder_name = os.path.splitext(os.path.basename(file_path))[0]
    os.makedirs(folder_name, exist_ok=True)
    output_file = os.path.join(folder_name, "analysis.txt")
    
    with open(output_file, 'w') as f:
        f.write(f"Analysis for {file_path}\n\n")
        for source_code, source_group in groups.items():
            for target_code, target_group in groups.items():
                if source_code != target_code:
                    reaching_count = count_reaching_nodes(graph, source_group, target_group)
                    f.write(f"{reaching_count}/{len(source_group)} Nodes in Group {source_code} have direct edges to Group {target_code}\n")
                    if reaching_count > 0:
                        non_reaching_nodes = find_non_reaching_nodes(graph, source_group, target_group)
                        if non_reaching_nodes:
                            node_tuples = [graph.nodes[node]['tuple'] for node in non_reaching_nodes]
                            f.write(f"Code {source_code} can reach Code {target_code}, but the following tuples cannot: " +
                                    ", ".join(f"<{t[0]},{t[1]}>" for t in node_tuples) + "\n")


def main():
    files_to_analyze = [
        "merged_graph_delayed_transformed.dot",
        "merged_graph_tuples_transformed.dot",
    ]

    for file_path in files_to_analyze:
        analyze_graph(file_path)


if __name__ == "__main__":
    main()
