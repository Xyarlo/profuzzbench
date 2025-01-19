#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd
from collections import defaultdict

def extract_column(output_dir, name_prefix, column_name):
    column_sets = []
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                # Look for 'state_stats.csv' in the archive
                member = next((member for member in tar.getmembers() if member.name.endswith("state_stats.csv")), None)
                if member:
                    tar.extract(member, output_dir)
                    extracted_csv_path = os.path.join(output_dir, member.name)

                    # Read the CSV and extract unique values from the specified column
                    data = pd.read_csv(extracted_csv_path)[column_name]
                    column_sets.append(set(data))

                    # Clean up the extracted file
                    os.remove(extracted_csv_path)

    if not column_sets:
        return None # No matching files found

    return column_sets


def compute_counts(column_sets):
    value_counts = defaultdict(int)
    for column_set in column_sets:
        for value in column_set:
            value_counts[value] += 1
    return value_counts


def merge_counts(counts_dicts, set_labels):
    # Combine all keys (unique values) from all sets
    all_values = set()
    for counts in counts_dicts:
        all_values.update(counts.keys())
    
    # Create a DataFrame with one row per unique value
    combined_df = pd.DataFrame({'response code': list(all_values)})

    # Add counts for each set label, defaulting missing counts to 0
    for counts, label in zip(counts_dicts, set_labels):
        combined_df[label] = combined_df['response code'].map(counts).fillna(0).astype(int)

    return combined_df


def main(csv_file, put, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    # Define set labels and the column to use for each
    sets = [
        {"label": "aflnet", "column": "id"},
        {"label": "aflnet-tuples", "column": "code2"},
        {"label": "tuples-random", "column": "code2"},
        {"label": "tuples-delayed", "column": "code2"},
        {"label": "tuples-compensated", "column": "code2"},
    ]

    counts_dicts = []
    set_labels = []

    for set_info in sets:
        label = set_info["label"]
        column_name = set_info["column"]
        print(f"Processing {label} using column '{column_name}'...")
        
        # Extract unique values from the specified column in all relevant CSV files
        column_sets = extract_column(output_folder, f"out-{put}-{label}_", column_name)

        if column_sets is None:
            print(f"Set {label} not found.")
            continue
        
        # Compute how many CSV files each unique value appears in
        value_counts = compute_counts(column_sets)
        counts_dicts.append(value_counts)
        set_labels.append(label)

    # Merge results into a single table
    combined_df = merge_counts(counts_dicts, set_labels)

    # Save the combined results to a CSV file
    output_file = os.path.join(output_folder, "combined_counts.csv")
    combined_df.to_csv(output_file, index=False)
    print(f"Saved combined results to {output_file}")


# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--csv_file',type=str,required=True,help="Full path to results.csv")
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")

    args = parser.parse_args()
    main(args.csv_file, args.put, args.output_folder)
