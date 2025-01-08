#!/usr/bin/env python

import argparse
import os
import tarfile
from pandas import read_csv
from pandas import DataFrame
from matplotlib import pyplot as plt
import pandas as pd
from statistics import mean


def calculate_phase_two_average(target, fuzzer, runs):
    phase_two_values = []

    for index in range(1, runs + 1):
        file_name = f"out-{target}-{fuzzer}_{index}.tar.gz"
        if not os.path.exists(file_name):
            print(f"Warning: {file_name} is missing.")
            continue

        try:
            with tarfile.open(file_name, "r:gz") as tar:
                fuzzer_stats_file = [
                    member for member in tar.getmembers() if "fuzzer_stats" in member.name
                ]
                if not fuzzer_stats_file:
                    print(f"Warning: No fuzzer_stats found in {file_name}")
                    return

                fuzzer_stats = tar.extractfile(fuzzer_stats_file[0])
                if fuzzer_stats is None:
                    print(f"Warning: Unable to extract fuzzer_stats from {file_name}")
                    return

                for line in fuzzer_stats:
                    decoded_line = line.decode("utf-8").strip()
                    if decoded_line.startswith("phase_two_start"):
                        phase_two_values.append(int(decoded_line.split(":")[1].strip()))
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
        return

    if not phase_two_values:
        print(f"Fuzzer: {fuzzer}, No valid phase_two_start values found.")
        return # No matching files found

    avg_phase_two_start = mean(phase_two_values)
    print(f"Fuzzer: {fuzzer}, Average phase_two_start: {avg_phase_two_start}")



    """
    # Initialize a dictionary to store phase_two_start values for each fuzzer
    phase_two_values = []

    # Iterate through files in the current directory
    for file_name in sorted(os.listdir(".")):
        if file_name.startswith(name_prefix) and file_name.endswith(".tar.gz"):
            try:
                # Open the .tar.gz file
                with tarfile.open(file_name, "r:gz") as tar:
                    # Extract fuzzer_stats file
                    fuzzer_stats_file = tar.extractfile("fuzzer_stats")
                    if fuzzer_stats_file:
                        # Read the content of the fuzzer_stats file
                        content = fuzzer_stats_file.read().decode('utf-8')

                        # Search for the phase_two_start line
                        match = re.search(r"phase_two_start\s+:\s+(\d+)", content)
                        if match:
                            phase_two_start = int(match.group(1))
                            # Append the value to the fuzzer's list
                            phase_two_values.append(phase_two_start)
            except (FileNotFoundError, tarfile.TarError) as e:
                print(f"Warning: Could not process file {file_name}: {e}")

    if not phase_two_values:
        print(f"Fuzzer: {fuzzer}, No valid phase_two_start values found.")
        return None  # No matching files found

    avg_phase_two_start = mean(values)
    print(f"Fuzzer: {fuzzer}, Average phase_two_start: {avg_phase_two_start}")
    """


def main(csv_file, put, runs, cut_off, step, output_folder):

    os.makedirs(output_folder, exist_ok=True)

    out_file = os.path.join(output_folder, "cov_over_time.png")
    out_file_stats = os.path.join(output_folder, "stats_over_time.png")

    # Read the results from CSV
    df = read_csv(csv_file)

    # Lists to store calculated mean and standard deviation data
    mean_list = []
    std_dev_list = []

    # Calculate mean and standard deviation for each time interval
    for subject in [put]:
        for fuzzer in ['aflnet', 'aflnet-tuples', 'tuples-random', "tuples-delayed"]:
            calculate_phase_two_average(subject, fuzzer, runs)
            for cov_type in ['b_abs', 'b_per', 'l_abs', 'l_per', 'states_abs', 'fuzzed_seeds']:
                # Get subject, fuzzer, and cov_type-specific DataFrame
                df1 = df[(df['subject'] == subject) & 
                         (df['fuzzer'] == fuzzer) & 
                         (df['cov_type'] == cov_type)]
                
                for time in range(1, cut_off + 1, step):
                    coverage_values = []
                    for run in range(1, runs + 1):
                        try:
                            # Get data for this specific run
                            df2 = df1[df1['run'] == run]
        
                            # Check if there are no rows for this run
                            if df2.empty:
                                continue
        
                            # Get the starting time for this run
                            start = df2.iloc[0, 0]
        
                            # Filter rows up to the cutoff time for this run
                            df3 = df2[df2['time'] <= start + time * 60]
        
                            # Ensure that there is at least one row of data after filtering
                            if df3.empty:
                                continue
        
                            # Append the last coverage value within this timeframe
                            coverage_values.append(df3.tail(1).iloc[0, 5])
    
                        except FileNotFoundError as e:
                            print(f"Warning: Missing file for run {run} of fuzzer '{fuzzer}' with coverage type '{cov_type}'. Skipping this run.")
                        except Exception as e:
                            print(f"Error processing run {run}: {e}. Skipping this run.")
                    # Calculate mean and standard deviation for this time interval
                    mean_cov = pd.Series(coverage_values).mean()
                    std_dev_cov = pd.Series(coverage_values).std()
                    
                    # Append results to lists
                    mean_list.append((subject, fuzzer, cov_type, time, mean_cov))
                    std_dev_list.append((subject, fuzzer, cov_type, time, std_dev_cov))
    
    # Convert lists to DataFrames
    mean_df = pd.DataFrame(mean_list, columns=['subject', 'fuzzer', 'cov_type', 'time', 'mean_cov'])
    std_dev_df = pd.DataFrame(std_dev_list, columns=['subject', 'fuzzer', 'cov_type', 'time', 'std_dev_cov'])
    # Merge mean and standard deviation DataFrames on common columns
    merged_df = pd.merge(mean_df, std_dev_df, on=['subject', 'fuzzer', 'cov_type', 'time'])
    # Set up a 2x2 grid for subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.flatten()  # Flatten to easily index axes in a loop

    fig.suptitle(f"Code Coverage Over Time for {put}", fontsize=16)
    # Define order for subplot titles
    coverage_types = ['b_abs', 'b_per', 'l_abs', 'l_per']
    
    # Iterate over coverage types and plot each in a separate subplot
    for i, cov_type in enumerate(coverage_types):
        ax = axes[i]
        cov_type_df = merged_df[merged_df['cov_type'] == cov_type]
        
        # Plot mean coverage with shaded standard deviation
        for fuzzer, fuzzer_df in cov_type_df.groupby('fuzzer'):
            ax.plot(fuzzer_df['time'], fuzzer_df['mean_cov'], label=f"{fuzzer}")
            ax.fill_between(fuzzer_df['time'],
                            fuzzer_df['mean_cov'] - fuzzer_df['std_dev_cov'],
                            fuzzer_df['mean_cov'] + fuzzer_df['std_dev_cov'],
                            alpha=0.3)  # Adjust alpha for transparency of shaded area
        # Set titles and labels for each subplot
        ax.set_xlabel("Time (minutes)")
        match cov_type:
            case 'b_abs':
                ax.set_ylabel("# edges")
            case 'b_per':
                ax.set_ylabel("% edges")
            case 'l_abs':
                ax.set_ylabel("# lines")
            case 'l_per':
                ax.set_ylabel("% lines")
            case _:
                ax.set_ylabel("unknown")
        ax.legend(loc='upper left')
        ax.grid(True)
    # Adjust layout to prevent overlap and save the figure
    plt.tight_layout()
    plt.savefig(out_file)


    ### Plot the additional `states_abs` and `fuzzed_seeds` metrics in a 1x2 grid
    fig_states_seeds, axes_states_seeds = plt.subplots(1, 2, figsize=(15, 5))

    metrics = ['states_abs', 'fuzzed_seeds']
    titles = ["Discovered States", "Total Fuzzed Seeds"]

    for i, (metric, title) in enumerate(zip(metrics, titles)):
        ax = axes_states_seeds[i]
        metric_df = merged_df[merged_df['cov_type'] == metric]
        
        for fuzzer, fuzzer_df in metric_df.groupby('fuzzer'):
            ax.plot(fuzzer_df['time'], fuzzer_df['mean_cov'], label=f"{fuzzer}")
            ax.fill_between(fuzzer_df['time'],
                            fuzzer_df['mean_cov'] - fuzzer_df['std_dev_cov'],
                            fuzzer_df['mean_cov'] + fuzzer_df['std_dev_cov'],
                            alpha=0.3)

        ax.set_title(f"{title} for {put}")
        ax.set_xlabel("Time (minutes)")
        match metric:
            case 'states_abs':
                ax.set_ylabel("# discovered states")
            case 'fuzzed_seeds':
                ax.set_ylabel("% fuzzed seeds")
            case _:
                ax.set_ylabel("unknown")
        ax.legend(loc='upper left')
        ax.grid(True)

    plt.tight_layout()
    plt.savefig(out_file_stats)

# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()    
    parser.add_argument('-i','--csv_file',type=str,required=True,help="Full path to results.csv")
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-r','--runs',type=int,required=True,help="Number of runs in the experiment")
    parser.add_argument('-c','--cut_off',type=int,required=True,help="Cut-off time in minutes")
    parser.add_argument('-s','--step',type=int,required=True,help="Time step in minutes")
    parser.add_argument('-o','--output_folder',type=str,required=True,help="Output folder")

    args = parser.parse_args()
    main(args.csv_file, args.put, args.runs, args.cut_off, args.step, args.output_folder)