#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def extract_csvs(output_dir, name_prefix):
    """
    Extracts the 'id' and 'scores' columns from 'state_stats.csv' in tar.gz files.
    Args:
        output_dir (str): Directory where extracted files are temporarily saved.
        name_prefix (str): Prefix of the tar.gz files to process (e.g., "out-aflnet-").
    Returns:
        list: A list of DataFrames containing 'id' and 'scores' columns.
    """
    csv_data = []
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                # Look for 'state_stats.csv' in the archive
                member = next(member for member in tar.getmembers() if member.name.endswith("state_stats.csv"))
                tar.extract(member, output_dir)
                extracted_csv_path = os.path.join(output_dir, member.name)

                # Read the CSV and extract the 'id' and 'scores' columns
                data = pd.read_csv(extracted_csv_path)[['id', 'score']]
                csv_data.append(data)

                # Clean up the extracted file
                os.remove(extracted_csv_path)
    return csv_data


def plot_distributions(data_list, set_label, bin_size=500, title_fontsize=14, label_fontsize=12, tick_fontsize=10,
                       output_file="distribution_plot.png"):
    """
    Plots the distribution of averaged scores grouped into ranges.
    Args:
        data_list (list): List of DataFrames with 'id' and 'scores' columns.
        set_label (str): Label for the set (e.g., "aflnet-tuples").
        bin_size (int): Size of the bins for grouping the scores.
        title_fontsize (int): Font size for the plot title.
        label_fontsize (int): Font size for the axis labels.
        tick_fontsize (int): Font size for the axis ticks.
        output_file (str): Output file path for the plot.
    """
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


def main(csv_file, put, step, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    set_labels = ["aflnet-tuples", "tuples-random"]

    for label in set_labels:
        print(f"Processing {label}...")
        # Extract CSV data for the current set
        set_data = extract_csvs(output_folder, f"out-{put}-{label}_")

        # Plot distributions of averaged scores
        output_file = os.path.join(output_folder, f"distribution_{label}.png")
        plot_distributions(set_data, label, step, output_file=output_file)


# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--csv_file',type=str,required=True,help="Full path to results.csv")
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-s','--step',type=int,required=True,help="Score step")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")

    args = parser.parse_args()
    main(args.csv_file, args.put, args.step, args.output_folder)
