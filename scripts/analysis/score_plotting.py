#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd
import matplotlib.pyplot as plt

def extract_csvs(output_dir, name_prefix, set_label):
    csv_data = []
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                member = next(member for member in tar.getmembers() if member.name.endswith("state_scores.csv"))
                tar.extract(member, output_dir)
                extracted_csv_path = os.path.join(output_dir, member.name)
                # Read the CSV and convert it to a Series
                data = pd.read_csv(extracted_csv_path, header=None).iloc[:, 0]
                csv_data.append(data)
                os.remove(extracted_csv_path)  # Clean up extracted file
    return csv_data

def plot_distributions(data_list, set_label, bin_size=500):
    all_numbers = pd.concat(data_list)
    max_value = all_numbers.max()
    bins = np.arange(0, max_value + bin_size, bin_size)

    plt.hist(all_numbers, bins=30, alpha=0.7, label=f"Set {set_label}")
    plt.xlabel("Range")
    plt.ylabel("Frequency")
    plt.title(f"Distribution of State Scores for {set_label}")
    plt.legend()

def main(csv_file, put, step, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    set_labels = {"aflnet-tuples","aflnet"}

    for label in set_labels:
        plt.figure(figsize=(12, 6))
        print(f"Processing {label}...")
        set_data = extract_csvs(output_folder, f"out-{put}-{label}_", label)
        plot_distributions(set_data, label, step)

        out_file = os.path.join(output_folder, f"score_distribution_{label}.png")
        plt.savefig(out_file)


# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()    
    parser.add_argument('-i','--csv_file',type=str,required=True,help="Full path to results.csv")
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-s','--step',type=int,required=True,help="Score step")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")

    args = parser.parse_args()
    main(args.csv_file, args.put, args.step, args.output_folder)
