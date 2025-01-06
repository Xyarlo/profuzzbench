#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd
import matplotlib.pyplot as plt


def extract_code_scores(output_dir, name_prefix, columns):
    data_frames = []
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                # Look for 'state_stats.csv' in the archive
                member = next(member for member in tar.getmembers() if member.name.endswith("state_stats.csv"))
                if member:
                    tar.extract(member, output_dir)
                    extracted_csv_path = os.path.join(output_dir, member.name)

                    # Read the CSV and extract specific columns
                    data = pd.read_csv(extracted_csv_path)[columns]
                    data_frames.append(data)

                    # Clean up the extracted file
                    os.remove(extracted_csv_path)

    if not data_frames:
        return None  # No matching files found

    combined_data = pd.concat(data_frames)

    # If 'id' exists, group by 'id' and average the scores
    if 'id' in combined_data.columns:
        combined_data = combined_data.groupby('id', as_index=False)['score'].mean().round(0)

    # If 'code2' exists, group by 'code2' and average the scores
    if 'code2' in combined_data.columns:
        combined_data = combined_data.groupby('code2', as_index=False)['score'].mean().round(0)

    return combined_data


def plot_scores(csv_file, output_folder):
    """
    Reads the resulting CSV, sorts the data, and creates a bar chart.
    Args:
        csv_file (str): Path to the CSV file with scores.
        output_folder (str): Path to save the bar chart.
    """
    # Read the CSV
    data = pd.read_csv(csv_file)

    # Exclude 'n/a' values and sort the data
    numeric_columns = data.columns[1:]  # Exclude 'code' column
    for col in numeric_columns:
        data[col] = pd.to_numeric(data[col], errors='coerce')  # Convert to numeric, set 'n/a' to NaN

    data.fillna(0, inplace=True)  # Replace NaN with 0 for plotting purposes
    data['average'] = data[numeric_columns].mean(axis=1)  # Calculate the average of all numeric columns
    data = data.sort_values(by='average')  # Sort by the average score

    # Plot the data
    plt.figure(figsize=(15, 8))
    bar_width = 0.2
    x = range(len(data['code']))

    for i, col in enumerate(numeric_columns):
        plt.bar([p + i * bar_width for p in x], data[col], bar_width, label=col)

    plt.xticks([p + bar_width for p in x], data['code'], rotation=90)
    plt.xlabel('Code', fontsize=12)
    plt.ylabel('Scores', fontsize=12)
    plt.title('Comparison of Scores Across Sets', fontsize=16)
    plt.legend()
    plt.tight_layout()

    # Save the bar chart
    chart_file = os.path.join(output_folder, "score_comparison_chart.png")
    plt.savefig(chart_file)
    plt.show()
    print(f"Bar chart saved to {chart_file}")


def main(put, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    
    sets = ['aflnet-tuples', 'tuples-delayed', 'tuples-random']

    # Extract data for aflnet
    print("Processing aflnet...")
    aflnet_data = extract_code_scores(output_folder, f"out-{put}-aflnet_", ['id', 'score'])
    aflnet_data.rename(columns={'id': 'code', 'score': 'aflnet'}, inplace=True)

    # Initialize the result DataFrame with aflnet data
    result = aflnet_data

    # Process other sets and merge averaged scores
    for label in sets:
        print(f"Processing {label}...")
        set_data = extract_code_scores(output_folder, f"out-{put}-{label}_", ['code2', 'score'])

        if set_data is None:
            print(f"Set {label} not found.")
            continue

        set_data.rename(columns={'code2': 'code', 'score': label}, inplace=True)
        result = pd.merge(result, set_data, on='code', how='outer')

    # Fill missing values with 'n/a'
    result.fillna('n/a', inplace=True)

    # Save the result to a new CSV file
    output_file = os.path.join(output_folder, "average_scores.csv")
    result.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

    # Create a bar chart from the resulting CSV
    plot_scores(output_file, output_folder)


# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()    
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")

    args = parser.parse_args()
    main(args.put, args.output_folder)
