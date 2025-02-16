#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def extract_code_scores(output_dir, name_prefix, column_name, global_order):
    data_frames = []
    
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                member = next((member for member in tar.getmembers() if member.name.endswith("state_stats.csv")), None)
                if member:
                    tar.extract(member, output_dir)
                    extracted_csv_path = os.path.join(output_dir, member.name)
                    data = pd.read_csv(extracted_csv_path)[['id', column_name]]
                    
                    grouped = data.groupby('id', as_index=False)[column_name].sum()
                    data_frames.append(grouped)
                    
                    global_order.extend(data['id'].tolist())
                    os.remove(extracted_csv_path)
    
    if not data_frames:
        return None
    
    combined_data = pd.concat(data_frames)
    combined_data = combined_data.groupby('id', as_index=False)[column_name].sum()
    return combined_data

def plot_scores(csv_file, output_folder, global_order):
    data = pd.read_csv(csv_file)
    data['code'] = pd.Categorical(data['code'], categories=global_order, ordered=True)
    data = data.sort_values(by='code')
    
    plt.figure(figsize=(15, 8))
    plt.bar(data['code'], data['value'])
    
    plt.xticks(rotation=90)
    plt.xlabel('Code', fontsize=12)
    plt.ylabel('Total Paths Credited', fontsize=12)
    plt.title('Comparison of Paths Credited Across Sets', fontsize=16)
    plt.tight_layout()
    
    chart_file = os.path.join(output_folder, "paths_credited_comparison.png")
    plt.savefig(chart_file)
    plt.show()
    print(f"Bar chart saved to {chart_file}")

def main(put, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    
    sets = {'aflnet': 'paths_discovered', 'generous-credits': 'paths'}
    global_order = []
    
    result = None
    for label, column_name in sets.items():
        print(f"Processing {label}...")
        set_data = extract_code_scores(output_folder, f"out-{put}-{label}_", column_name, global_order)
        if set_data is None:
            print(f"Set {label} not found.")
            continue
        set_data.rename(columns={'id': 'code', column_name: 'value'}, inplace=True)
        result = set_data if result is None else pd.merge(result, set_data, on='code', how='outer')
    
    global_order = list(dict.fromkeys(global_order))
    result.fillna('n/a', inplace=True)
    output_file = os.path.join(output_folder, "average_paths_credited.csv")
    result.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")
    
    plot_scores(output_file, output_folder, global_order)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")
    args = parser.parse_args()
    main(args.put, args.output_folder)
