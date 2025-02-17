#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def extract_csvs(output_dir, name_prefix):
    csv_data = []
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                # Look for 'state_stats.csv' in the archive
                member = next((member for member in tar.getmembers() if member.name.endswith("state_stats.csv")), None)
                if member:
                    tar.extract(member, output_dir)
                    extracted_csv_path = os.path.join(output_dir, member.name)
                
                    # Read the CSV and extract the 'id' and 'scores' columns
                    data = pd.read_csv(extracted_csv_path)[['id', 'score']]
                    csv_data.append(data)
                
                    os.remove(extracted_csv_path)
                    parent_dir = Path(output_dir) / Path(member.name).parent
                    while parent_dir != Path(output_dir):
                        try:
                            parent_dir.rmdir()
                        except OSError:
                            break
                        parent_dir = parent_dir.parent

    if not csv_data:
        return None # No matching files found

    return csv_data


def plot_distributions(data_list, set_label, bin_size=500, title_fontsize=14, label_fontsize=12, tick_fontsize=10,
                       output_file="distribution_plot.png"):
    # Combine all data into a single DataFrame
    combined_data = pd.concat(data_list)

    # Compute average scores for each 'id'
    average_scores = combined_data.groupby('id', as_index=False)['score'].mean()

    # Bin the averaged scores
    max_score = average_scores['score'].max()
    bins = np.arange(0, max_score + bin_size, bin_size)
    
    # Plot the histogram of binned averages
    plt.figure(figsize=(12, 6))
    plt.hist(average_scores['score'], bins=bins, alpha=0.7, label=f"Set {set_label}", edgecolor="black")
    plt.xlabel(f"Score Ranges (Bin Size: {bin_size})", fontsize=label_fontsize)
    plt.ylabel("Bucket Size (Frequency)", fontsize=label_fontsize)
    plt.title(f"Distribution of Averaged Scores in {set_label}", fontsize=title_fontsize)
    plt.xticks(fontsize=tick_fontsize)
    plt.yticks(fontsize=tick_fontsize)
    plt.legend()
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_file)


def main(put, step, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    set_labels = ["aflnet", "aflnet-random", "aflnet-tuples", "tuples-random", "tuples-delayed", "tuples-compensated", "faster-havoc", "no-penalty", 'delayed-feedback', 'queue-compensation', 'generous-credits']

    for label in set_labels:
        print(f"Processing {label}...")
        # Extract CSV data for the current set
        set_data = extract_csvs(output_folder, f"out-{put}-{label}_")

        if set_data is None:
            print(f"Set {label} not found.")
            continue

        # Plot distributions of averaged scores
        output_file = os.path.join(output_folder, f"distribution_{label}.png")
        plot_distributions(set_data, label, step, output_file=output_file)


# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()    
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-s','--step',type=int,required=True,help="Score step")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")

    args = parser.parse_args()
    main(args.put, args.step, args.output_folder)
