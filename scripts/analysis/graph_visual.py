#!/usr/bin/env python3

import graphviz
import sys
import os

def save_dot_to_png(input_file):
    # Check if the input file exists and is a .dot file
    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        return

    if not input_file.endswith(".dot"):
        print("Error: The input file must have a .dot extension.")
        return

    try:
        # Extract filename without extension
        filename = os.path.splitext(os.path.basename(input_file))[0]
        
        # Create a Graphviz object and render the DOT file
        graph = graphviz.Source.from_file(input_file)
        
        # Save the graph as a PNG file in the current directory
        output_file = filename + ".png"
        graph.render(filename=filename, format="png", cleanup=True)
        
        print(f"Graph successfully saved as '{output_file}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Check if a file name is provided as a command line argument
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_file.dot>")
    else:
        input_file = sys.argv[1]
        save_dot_to_png(input_file)
