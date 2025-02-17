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
                # Look for 'state_stats.csv' in the archive
                member = next((m for m in tar.getmembers() if m.name.endswith("state_stats.csv")), None)
                if member:
                    tar.extract(member, output_dir)
                    extracted_csv_path = os.path.join(output_dir, member.name)

                    # Read the CSV and extract the 'id' and 'selected_times' columns
                    data = pd.read_csv(extracted_csv_path)[['id', 'selected_times']]
                    csv_data.append(data)

                    # Clean up the extracted file
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

    # Combine all data and compute averages for 'selected_times' grouped by 'id'
    combined_data = pd.concat(csv_data)
    averaged_data = combined_data.groupby('id', as_index=False)['selected_times'].mean()

    return averaged_data

def plot_boxplot(data_list, set_label, output_file):
    
    plt.figure(figsize=(12, 6))
    
    # Extract 'selected_times' data for boxplot
    boxplot_data = [data['selected_times'] for data in data_list]

    # Create the horizontal boxplot
    plt.boxplot(boxplot_data, tick_labels=[f"Set {set_label}"], vert=False, patch_artist=True, 
                boxprops=dict(facecolor='skyblue', color='black'))
    plt.xlabel("Selected Times (Averaged)", fontsize=12)
    plt.title(f"Boxplot of Selected Times by ID in {set_label}", fontsize=16)
    plt.xlim(left=0)  # Force x-axis to start at 0
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(output_file)

def main(put, output_folder):

    os.makedirs(output_folder, exist_ok=True)

    set_labels = ["aflnet", "aflnet-random", "aflnet-tuples", "tuples-random", "tuples-delayed", "tuples-compensated", "faster-havoc", "no-penalty", 'delayed-feedback', 'queue-compensation', 'generous-credits', 'no-splicing']

    for label in set_labels:
        print(f"Processing {label}...")
        # Extract CSV data for the current set
        set_data = extract_csvs(output_folder, f"out-{put}-{label}_")
        
        if set_data is None:
            print(f"Set {label} not found.")
            continue
        
        # Plot boxplot for selected_times
        output_file = os.path.join(output_folder, f"selected_times_{label}.png")
        plot_boxplot([set_data], label, output_file)

# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")

    args = parser.parse_args()
    main(args.put, args.output_folder)
