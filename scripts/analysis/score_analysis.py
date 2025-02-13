#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def extract_code_scores(output_dir, name_prefix, columns, variable):
    data_frames = []
    order_scores = {}  # Dictionary to store rank scores

    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                member = next((member for member in tar.getmembers() if member.name.endswith("state_stats.csv")), None)
                if member:
                    tar.extract(member, output_dir)
                    extracted_csv_path = os.path.join(output_dir, member.name)
                    data = pd.read_csv(extracted_csv_path)[columns]

                    group_column = 'id' if 'id' in data.columns else 'code2'

                    # Assign an "order score" based on appearance order in the CSV
                    for rank, value in enumerate(data[group_column]):
                        if value not in order_scores:
                            order_scores[value] = []
                        order_scores[value].append(rank)

                    # Aggregate variable
                    if variable == 'score':
                        data = data.groupby(group_column, as_index=False)[variable].mean()
                    else:
                        data = data.groupby(group_column, as_index=False)[variable].sum()

                    data_frames.append(data)
                    os.remove(extracted_csv_path)

    if not data_frames:
        return None

    combined_data = pd.concat(data_frames)
    group_column = 'id' if 'id' in combined_data.columns else 'code2'

    # Compute the dominant ranking by taking the average order position
    rank_df = pd.DataFrame([(key, sum(positions) / len(positions)) 
                            for key, positions in order_scores.items()], 
                            columns=[group_column, 'rank_score'])

    # Merge ranking information into the dataset
    combined_data = combined_data.groupby(group_column, as_index=False)[variable].mean().round(0)
    combined_data = combined_data.merge(rank_df, on=group_column, how='left')

    return combined_data

def plot_scores(csv_file, output_folder, variable):
    data = pd.read_csv(csv_file)

    # Remove irrelevant columns
    data.drop(columns=[col for col in data.columns if 'row_index' in col], inplace=True, errors='ignore')

    # Convert numerical columns
    numeric_columns = data.columns[1:]
    for col in numeric_columns:
        data[col] = pd.to_numeric(data[col], errors='coerce')

    data.fillna(0, inplace=True)
    data['average'] = data[numeric_columns].mean(axis=1)

    # Ensure sorting by rank score (correct order) before plotting
    if 'rank_score' in data.columns:
        data = data.sort_values(by='rank_score')

    plt.figure(figsize=(15, 8))
    bar_width = 0.2
    x = range(len(data['code']))

    for i, col in enumerate(numeric_columns):
        plt.bar([p + i * bar_width for p in x], data[col], bar_width, label=col)

    plt.xticks([p + bar_width for p in x], data['code'], rotation=90)
    plt.xlabel('Code', fontsize=12)
    plt.ylabel(f'avg_{variable}', fontsize=12)
    plt.title(f'Comparison of {variable} Across Sets', fontsize=16)
    plt.legend()
    plt.tight_layout()

    chart_file = os.path.join(output_folder, f"{variable}_comparison_chart.png")
    plt.savefig(chart_file)
    plt.show()
    print(f"Bar chart saved to {chart_file}")

def main(put, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    
    aflnet_sets = ['aflnet', 'generous-credits' , 'no-penalty', 'delayed-feedback', 'queue-compensation']
    tuples_sets = ['aflnet-tuples', 'tuples-delayed', 'tuples-random', 'tuples-compensated', 'faster-havoc']
    
    variables = ['score', 'selected_times', 'fuzzs', 'paths_discovered']
    
    for variable in variables:
        print("Processing aflnet-like sets...")
        result = None
        for label in aflnet_sets:
            print(f"Processing {label}...")
            set_data = extract_code_scores(output_folder, f"out-{put}-{label}_", ['id', variable], variable)
            if set_data is None:
                print(f"Set {label} not found.")
                continue
            set_data.rename(columns={'id': 'code', variable: label}, inplace=True)
            result = set_data if result is None else pd.merge(result, set_data, on='code', how='outer')
        
        for label in tuples_sets:
            print(f"Processing {label}...")
            set_data = extract_code_scores(output_folder, f"out-{put}-{label}_", ['code2', variable], variable)
            if set_data is None:
                print(f"Set {label} not found.")
                continue
            set_data.rename(columns={'code2': 'code', variable: label}, inplace=True)
            result = result if result is not None else set_data
            result = pd.merge(result, set_data, on='code', how='outer')
        
        # Remove any 'row_index' columns before saving
        result.drop(columns=[col for col in result.columns if 'row_index' in col], inplace=True, errors='ignore')

        result.fillna('n/a', inplace=True)
        output_file = os.path.join(output_folder, f"average_{variable}.csv")
        result.to_csv(output_file, index=False)
        print(f"Results saved to {output_file}")
        
        plot_scores(output_file, output_folder, variable)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")
    args = parser.parse_args()
    main(args.put, args.output_folder)
