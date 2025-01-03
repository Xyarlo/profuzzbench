#!/usr/bin/env python

import os
import tarfile
import pandas as pd


def extract_code_scores(output_dir, name_prefix, columns):
    """
    Extracts specific columns from 'state_stats.csv' in tar.gz files.
    Args:
        output_dir (str): Directory where extracted files are temporarily saved.
        name_prefix (str): Prefix of the tar.gz files to process (e.g., "out-aflnet-").
        columns (list): List of columns to extract (e.g., ['code2', 'score']).
    Returns:
        DataFrame: A DataFrame containing the extracted columns, averaged if necessary.
    """
    data_frames = []
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            with tarfile.open(file_name, "r:gz") as tar:
                # Look for 'state_stats.csv' in the archive
                member = next(member for member in tar.getmembers() if member.name.endswith("state_stats.csv"))
                tar.extract(member, output_dir)
                extracted_csv_path = os.path.join(output_dir, member.name)

                # Read the CSV and extract specific columns
                data = pd.read_csv(extracted_csv_path)[columns]
                data_frames.append(data)

                # Clean up the extracted file
                os.remove(extracted_csv_path)

    combined_data = pd.concat(data_frames)

    # If 'code2' exists, group by 'code2' and average the scores
    if 'code2' in combined_data.columns:
        combined_data = combined_data.groupby('code2', as_index=False)['score'].mean()

    return combined_data


def main(put, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    
    sets = ['aflnet-tuples', 'tuples-delayed']

    # Extract data for aflnet
    print("Processing aflnet...")
    aflnet_data = extract_code_scores(output_folder, "out-aflnet", ['id', 'score'])

    # Map id to score for aflnet
    aflnet_scores = dict(zip(aflnet_data['id'], aflnet_data['score']))

    # Prepare the result DataFrame
    result = pd.DataFrame({'code': aflnet_data['id'], 'aflnet': aflnet_data['score']})

    # Process other sets and map averaged scores to the corresponding codes
    for set_name in sets:
        print(f"Processing {set_name}...")
        set_data = extract_code_scores(output_folder, f"out-{set_name}", ['code2', 'score'])
        set_scores = dict(zip(set_data['code2'], set_data['score']))
        result[set_name] = result['code'].map(set_scores)

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
