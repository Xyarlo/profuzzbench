#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd
import matplotlib.pyplot as plt

def extract_csvs(output_dir, name_prefix):
    """
    Extracts the 'id' and 'selected_times' columns from 'state_stats.csv' in tar.gz files.
    Args:
        output_dir (str): Directory where extracted files are temporarily saved.
        name_prefix (str): Prefix of the tar.gz files to process (e.g., "out-aflnet-").
    Returns:
        DataFrame: A DataFrame containing 'id' and averaged 'selected_times'.
    """
    csv_data = []
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                # Look for 'state_stats.csv' in the archive
                member = next(member for member in tar.getmembers() if member.name.endswith("state_stats.csv"))
                tar.extract(member, output_dir)
                extracted_csv_path = os.path.join(output_dir, member.name)

                # Read the CSV and extract the 'id' and 'selected_times' columns
                data = pd.read_csv(extracted_csv_path)[['id', 'selected_times']]
                csv_data.append(data)

                # Clean up the extracted file
                os.remove(extracted_csv_path)

    # Combine all data and compute averages for 'selected_times' grouped by 'id'
    combined_data = pd.concat(csv_data)
    averaged_data = combined_data.groupby('id', as_index=False)['selected_times'].mean()

    return averaged_data

def plot_boxplot(data_list, set_label, output_file):
    """
    Plots a horizontally oriented boxplot of 'selected_times' grouped by 'id' for each set.
    Args:
        data_list (list): List of DataFrames with 'id' and averaged 'selected_times'.
        set_label (str): Label for the set (e.g., "aflnet-tuples").
        output_file (str): Output file path for the plot.
    """
    plt.figure(figsize=(12, 6))
    
    # Extract 'selected_times' data for boxplot
    boxplot_data = [data['selected_times'] for data in data_list]

    # Create the horizontal boxplot
    plt.boxplot(boxplot_data, labels=[f"Set {set_label}"], vert=False, patch_artist=True, 
                boxprops=dict(facecolor='skyblue', color='black'))
    plt.xlabel("Selected Times (Averaged)", fontsize=12)
    plt.title(f"Boxplot of Selected Times by ID in {set_label}", fontsize=16)
    plt.xlim(left=0)  # Force x-axis to start at 0
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(output_file)

def main(csv_file, put, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    set_labels = ["aflnet-tuples", "tuples-random"]

    for label in set_labels:
        print(f"Processing {label}...")
        # Extract CSV data for the current set
        set_data = extract_csvs(output_folder, f"out-{put}-{label}_")
        
        # Plot boxplot for selected_times
        output_file = os.path.join(output_folder, f"selected_times_{label}.png")
        plot_boxplot([set_data], label, output_file)

# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--csv_file',type=str,required=True,help="Full path to results.csv")
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")

    args = parser.parse_args()
    main(args.csv_file, args.put, args.output_folder)
