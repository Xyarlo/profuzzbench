#!/usr/bin/env python

import argparse
import os
import tarfile
import pandas as pd


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

    # If 'code2' exists, group by 'code2' and average the scores
    if 'code2' in combined_data.columns:
        combined_data = combined_data.groupby('code2', as_index=False)['score'].mean()

    return combined_data


def main(put, output_folder):

    os.makedirs(output_folder, exist_ok=True)
    
    sets = ['aflnet', 'aflnet-tuples', 'tuples-delayed', 'tuples-random']

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
    output_file = os.path.join(output_folder, "score_comparison.csv")
    result.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")


# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()    
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")

    args = parser.parse_args()
    main(args.put, args.output_folder)
