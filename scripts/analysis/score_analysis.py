#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def extract_code_scores(output_dir, name_prefix, columns, variable):
    data_frames = []
    rank_records = []
    
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                member = next((member for member in tar.getmembers() if member.name.endswith("state_stats.csv")), None)
                if member:
                    tar.extract(member, output_dir)
                    extracted_csv_path = os.path.join(output_dir, member.name)
                    data = pd.read_csv(extracted_csv_path)[columns]
                    
                    group_column = 'id' if 'id' in data.columns else 'code2'
                    data['rank'] = data.reset_index().index  # Store the row index as rank
                    
                    if variable == 'score':
                        grouped = data.groupby(group_column, as_index=False).agg({variable: 'mean', 'rank': 'median'})
                    else:
                        grouped = data.groupby(group_column, as_index=False).agg({variable: 'sum', 'rank': 'median'})
                    
                    data_frames.append(grouped)
                    rank_records.append(grouped[['rank', group_column]])
                    
                    os.remove(extracted_csv_path)
                    parent_dir = Path(output_dir) / Path(member.name).parent
                    while parent_dir != Path(output_dir):
                        try:
                            parent_dir.rmdir()
                        except OSError:
                            break
                        parent_dir = parent_dir.parent
    
    if not data_frames:
        return None
    
    combined_data = pd.concat(data_frames)
    rank_data = pd.concat(rank_records)
    
    group_column = 'id' if 'id' in combined_data.columns else 'code2'
    median_ranks = rank_data.groupby(group_column)['rank'].median().reset_index()
    
    combined_data = combined_data.groupby(group_column, as_index=False).agg({variable: 'mean'})
    combined_data = combined_data.merge(median_ranks, on=group_column, how='left')
    combined_data = combined_data.sort_values(by='rank').drop(columns=['rank'])  # Sort by median rank
    
    return combined_data

def plot_scores(csv_file, output_folder, variable):
    data = pd.read_csv(csv_file)
    numeric_columns = data.columns[1:]
    for col in numeric_columns:
        data[col] = pd.to_numeric(data[col], errors='coerce')
    
    data.fillna(0, inplace=True)
    data['average'] = data[numeric_columns].mean(axis=1)
    
    # Sort by median rank of IDs (precomputed in extract_code_scores)
    data = data.sort_values(by='average', ascending=False)
    
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
