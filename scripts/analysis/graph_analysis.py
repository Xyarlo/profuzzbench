#!/usr/bin/env python3

import networkx as nx
import re

def parse_dot_file(file_path):
    """Parse a DOT file and return a directed graph with tuple-labeled nodes."""
    graph = nx.DiGraph()
    node_label_pattern = re.compile(r'(\w+) \[label="<(?P<first>\d+),(?P<second>\d+)>"\];')

    with open(file_path, 'r') as f:
        for line in f:
            # Parse nodes with labels
            match = node_label_pattern.search(line)
            if match:
                node_id = match.group(1)
                first = int(match.group('first'))
                second = int(match.group('second'))
                graph.add_node(node_id, tuple=(first, second))

            # Parse edges
            edge_match = re.match(r'(\w+) -> (\w+);', line)
            if edge_match:
                source = edge_match.group(1)
                target = edge_match.group(2)
                graph.add_edge(source, target)

    # Debugging outputs to check parsed nodes and edges
    print("Parsed Nodes with Attributes:", graph.nodes(data=True))
    print("Parsed Edges:", list(graph.edges()))

    return graph

def group_nodes_by_second(graph):
    """Group nodes by the second value in their tuple label."""
    groups = {}
    for node, data in graph.nodes(data=True):
        _, second = data['tuple']
        groups.setdefault(second, []).append(node)
    return groups

def can_reach_any(graph, source_group, target_group):
    """Check if any node in source_group can reach any node in target_group."""
    for source in source_group:
        for target in target_group:
            if nx.has_path(graph, source, target):
                return True
    return False

def count_reaching_nodes(graph, source_group, target_group):
    """Count how many nodes in source_group can reach any node in target_group."""
    count = 0
    for source in source_group:
        if any(nx.has_path(graph, source, target) for target in target_group):
            count += 1
    return count

def find_non_reaching_node(graph, source_group, target_group):
    """Find a node in source_group that cannot reach any node in target_group."""
    for source in source_group:
        if not any(nx.has_path(graph, source, target) for target in target_group):
            return source
    return None

def analyze_graph(file_path):
    """Analyze the graph for group-to-group reachability and print results."""
    print(f"Analyzing graph: {file_path}")

    # Parse the graph and group nodes
    graph = parse_dot_file(file_path)
    groups = group_nodes_by_second(graph)

    # Perform analysis
    for source_code, source_group in groups.items():
        for target_code, target_group in groups.items():
            if source_code != target_code:
                reaching_count = count_reaching_nodes(graph, source_group, target_group)
                print(f"{reaching_count}/{len(source_group)} Nodes in Group {source_code} are able to reach Group {target_code}")
                if reaching_count > 0:
                    non_reaching_node = find_non_reaching_node(graph, source_group, target_group)
                    if non_reaching_node:
                        node_tuple = graph.nodes[non_reaching_node]['tuple']
                        print(f"Code {source_code} can reach Code {target_code}, but Tuple <{node_tuple[0]},{node_tuple[1]}> cannot.")

def main():
    # List of transformed DOT files to analyze
    files_to_analyze = [
        "merged_graph_delayed_transformed.dot",
        "merged_graph_compensated_transformed.dot",
        "merged_graph_tuples_transformed.dot",
    ]

    for file_path in files_to_analyze:
        analyze_graph(file_path)

if __name__ == "__main__":
    main()
