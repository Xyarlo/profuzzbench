#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd


def extract_csvs(output_dir, name_prefix):
    csv_data = []
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                # Look for 'state_stats.csv' in the archive
                member = next(member for member in tar.getmembers() if member.name.endswith("state_stats.csv"))
                if member:
                    tar.extract(member, output_dir)
                    extracted_csv_path = os.path.join(output_dir, member.name)

                    # Read the CSV and extract relevant columns
                    data = pd.read_csv(extracted_csv_path)[['id', 'code2', 'score']]
                    csv_data.append(data)

                    # Clean up the extracted file
                    os.remove(extracted_csv_path)

    if not csv_data:
        return None # No matching files found

    return csv_data


def compute_grouped_statistics(data_list):
    # Combine all data into a single DataFrame
    combined_data = pd.concat(data_list)
    
    # Compute average score for each 'id'
    averaged_score = combined_data.groupby(['id', 'code2'], as_index=False)['score'].mean()
    
    # Group by 'code2' and compute statistics
    grouped_stats = averaged_score.groupby('code2', as_index=False).agg(
        substates=('id', 'count'),           # Count of 'id' per group
        avg_score=('score', 'mean'),       # Mean of score
        std_dev=('score', 'std'),          # Standard deviation of score
        min_score=('score', 'min'),        # Minimum score
        max_score=('score', 'max')         # Maximum score
    )
    
    # Add the spread column (max_score - min_score)
    grouped_stats['spread'] = grouped_stats['max_score'] - grouped_stats['min_score']
    
    # Round numerical values to 1 decimal place
    grouped_stats = grouped_stats.round({
        'avg_score': 1,
        'std_dev': 1,
        'min_score': 1,
        'max_score': 1,
        'spread': 1
    })
    
    # Rename 'code2' to 'state' for output consistency
    grouped_stats.rename(columns={'code2': 'state'}, inplace=True)
    
    # Sort by 'spread' in descending order
    grouped_stats = grouped_stats.sort_values(by='spread', ascending=False)
    
    return grouped_stats


def main(put, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    set_labels = ["aflnet-tuples", "tuples-delayed", "tuples-compensated"]

    for label in set_labels:
        # Extract data for the aflnet-tuples set
        print(f"Processing {label}...")
        set_data = extract_csvs(output_folder, f"out-{put}-{label}_")

        if set_data is None:
            print(f"Set {label} not found.")
            continue
    
        # Compute grouped statistics
        grouped_stats = compute_grouped_statistics(set_data)
    
        # Save the results to a CSV file
        output_file = os.path.join(output_folder, f"state_statistics_{label}.csv")
        grouped_stats.to_csv(output_file, index=False)
        print(f"Statistics saved to {output_file}")


# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")

    args = parser.parse_args()
    main(args.put, args.output_folder)
