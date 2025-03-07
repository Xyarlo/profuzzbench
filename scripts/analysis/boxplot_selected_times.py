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

                    # Read the CSV and extract required columns
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

    # Combine all data and compute averages for 'selected_times' and 'score' grouped by 'id'
    combined_data = pd.concat(csv_data)
    averaged_data = combined_data.groupby('id', as_index=False).mean()

    return averaged_data


def plot_variable_boxplots(data_dict, variable, output_file):
    num_sets = len(data_dict)
    fig, axes = plt.subplots(nrows=num_sets, ncols=1, figsize=(12, max(2, 3 * num_sets)))
    fig.suptitle(f"Boxplot of {variable.capitalize()} Across Different Sets", fontsize=18)

    if num_sets == 1:
        axes = [axes]  # Ensure axes is iterable even for one plot

    for ax, (label, data) in zip(axes, data_dict.items()):
        ax.boxplot(data[variable], vert=False, patch_artist=True,
                   boxprops=dict(facecolor='skyblue', color='black'))
        ax.set_xlabel(f"{variable.capitalize()} (Averaged)", fontsize=12)
        ax.set_yticks([])  # Remove numerical tick labels on the y-axis
        ax.set_ylabel(label, fontsize=10)
        ax.set_xlim(left=0)
        ax.set_ylim(0.8, 1.2)  # Keep plot height constrained without squashing boxes

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)


def main(put, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    set_labels = ["aflnet", "aflnet-random", "aflnet-tuples", "tuples-random", "tuples-delayed", "tuples-compensated",
                  "faster-havoc", "no-penalty", 'delayed-feedback', 'queue-compensation', 'generous-credits', 'no-splicing']

    data_dict = {}
    for label in set_labels:
        print(f"Processing {label}...")
        set_data = extract_csvs(output_folder, f"out-{put}-{label}_")

        if set_data is None:
            print(f"Set {label} not found.")
            continue

        data_dict[label] = set_data

    if data_dict:
        plot_variable_boxplots(data_dict, 'selected_times', os.path.join(output_folder, "boxplots_selected_times.png"))
        plot_variable_boxplots(data_dict, 'score', os.path.join(output_folder, "boxplots_score.png"))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--put', type=str, required=True, help="Name of the subject program")
    parser.add_argument('-o', '--output_folder', type=str, required=True, help="Output folder")
    args = parser.parse_args()
    main(args.put, args.output_folder)
