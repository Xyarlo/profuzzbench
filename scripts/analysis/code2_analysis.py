#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd
from collections import defaultdict

def extract_code2(output_dir, name_prefix):
    """
    Extracts the 'code2' column from 'state_stats.csv' in tar.gz files.
    Args:
        output_dir (str): Directory where extracted files are temporarily saved.
        name_prefix (str): Prefix of the tar.gz files to process (e.g., "out-aflnet-").
    Returns:
        list: A list of sets containing unique 'code2' values from each CSV file.
    """
    code2_sets = []
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                # Look for 'state_stats.csv' in the archive
                member = next(member for member in tar.getmembers() if member.name.endswith("state_stats.csv"))
                tar.extract(member, output_dir)
                extracted_csv_path = os.path.join(output_dir, member.name)

                # Read the CSV and extract unique 'code2' values
                data = pd.read_csv(extracted_csv_path)['code2']
                code2_sets.append(set(data))

                # Clean up the extracted file
                os.remove(extracted_csv_path)
    return code2_sets

def compute_code2_counts(code2_sets):
    """
    Computes how many CSV files each 'code2' appears in.
    Args:
        code2_sets (list): List of sets containing unique 'code2' values from each file.
    Returns:
        dict: Dictionary where keys are 'code2' values and values are the counts.
    """
    code2_counts = defaultdict(int)
    for code2_set in code2_sets:
        for code2 in code2_set:
            code2_counts[code2] += 1
    return code2_counts

def merge_counts(counts_dicts, set_labels):
    """
    Merges counts from multiple sets into a single table.
    Args:
        counts_dicts (list): List of dictionaries with 'code2' counts for each set.
        set_labels (list): List of set labels corresponding to the dictionaries.
    Returns:
        DataFrame: A DataFrame combining counts for all sets.
    """
    # Combine all keys (code2 values) from all sets
    all_code2 = set()
    for counts in counts_dicts:
        all_code2.update(counts.keys())
    
    # Create a DataFrame with one row per code2
    combined_df = pd.DataFrame({'code2': list(all_code2)})

    # Add counts for each set label, defaulting missing counts to 0
    for counts, label in zip(counts_dicts, set_labels):
        combined_df[label] = combined_df['code2'].map(counts).fillna(0).astype(int)

    return combined_df

def main(csv_file, put, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    set_labels = ["aflnet-tuples", "tuples-random"]
    counts_dicts = []

    for label in set_labels:
        print(f"Processing {label}...")
        # Extract unique 'code2' values from all relevant CSV files
        code2_sets = extract_code2(output_folder, f"out-{put}-{label}_")
        
        # Compute how many CSV files each 'code2' appears in
        code2_counts = compute_code2_counts(code2_sets)
        counts_dicts.append(code2_counts)

    # Merge results into a single table
    combined_df = merge_counts(counts_dicts, set_labels)

    # Save the combined results to a CSV file
    output_file = os.path.join(output_folder, "combined_code2_counts.csv")
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
