#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def extract_csvs(output_dir, name_prefix):
    csv_data = []
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                member = next((m for m in tar.getmembers() if m.name.endswith("state_stats.csv")), None)
                if member:
                    tar.extract(member, output_dir)
                    extracted_csv_path = os.path.join(output_dir, member.name)
                    
                    # Read the CSV and extract relevant columns
                    data = pd.read_csv(extracted_csv_path)[['id', 'selected_times', 'score']]
                    csv_data.append(data)
                    
                    # Clean up extracted file
                    os.remove(extracted_csv_path)
                    parent_dir = Path(output_dir) / Path(member.name).parent
                    while parent_dir != Path(output_dir):
                        try:
                            parent_dir.rmdir()
                        except OSError:
                            break
                        parent_dir = parent_dir.parent
    
    if not csv_data:
        return None  # No matching files found

    # Combine all data and compute averages grouped by 'id'
    combined_data = pd.concat(csv_data)
    averaged_data = combined_data.groupby('id', as_index=False).mean()
    
    return averaged_data

def plot_boxplot(data_list, set_labels, output_file, variable, xlabel):
    plt.figure(figsize=(12, 6))
    
    actual_data = [data[variable] for data in data_list]
    labels = [f"{label}" for label in set_labels]
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    boxplot = ax1.boxplot(actual_data, labels=labels, vert=False, patch_artist=True, boxprops=dict(facecolor='skyblue', color='black'))
    ax1.set_xlabel(xlabel, fontsize=12)
    ax1.set_title(f"Comparison of {xlabel} Across Sets", fontsize=16)
    
    # Compute adjusted x-limits for each set
    min_values = [data.min() for data in actual_data]
    max_values = [data.max() for data in actual_data]
    adjusted_max_values = [max_val * 1.05 for max_val in max_values]  # Add 5% padding to max value
    
    # Ensure all plots start at 0 and maintain proportional width
    ax1.set_xlim(0, max(adjusted_max_values))
    
    # Add individual x-axes dynamically
    if len(set_labels) == 1:
        ax1.set_xlim(0, adjusted_max_values[0])
        ax1.set_xlabel(f"Actual Values for {set_labels[0]}", fontsize=12)
    elif len(set_labels) == 2:
        ax1.set_xlim(0, max(adjusted_max_values))
        ax1.set_xlabel(f"Actual Values for {set_labels[0]}", fontsize=12)
        ax2 = ax1.twiny()
        ax2.set_xlim(0, adjusted_max_values[1])
        ax2.set_xlabel(f"Actual Values for {set_labels[1]}", fontsize=12)
    else:
        for i, (data, label, adj_max) in enumerate(zip(actual_data, set_labels, adjusted_max_values)):
            ax_extra = ax1.twiny()
            ax_extra.set_xlim(0, adj_max)
            ax_extra.spines['top'].set_position(('outward', 40 * i))
            ax_extra.set_xlabel(f"Actual Values for {label}", fontsize=12)
    
    plt.tight_layout()
    plt.savefig(output_file)

def main(put, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    set_labels = ["aflnet", "aflnet-random", "aflnet-tuples", "tuples-random", "tuples-delayed", "tuples-compensated", "faster-havoc", "no-penalty", "delayed-feedback", "queue-compensation", "generous-credits", "no-splicing"]
    
    data_list = []
    actual_labels = []
    for label in set_labels:
        print(f"Processing {label}...")
        set_data = extract_csvs(output_folder, f"out-{put}-{label}_")
        
        if set_data is None:
            print(f"Set {label} not found.")
            continue
        
        data_list.append(set_data)
        actual_labels.append(label)
    
    if data_list:
        plot_boxplot(data_list, actual_labels, os.path.join(output_folder, "selected_times_boxplot.png"), 'selected_times', "Selected Times")
        plot_boxplot(data_list, actual_labels, os.path.join(output_folder, "score_boxplot.png"), 'score', "Score")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")
    args = parser.parse_args()
    main(args.put, args.output_folder)
