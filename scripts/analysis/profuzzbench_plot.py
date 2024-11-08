#!/usr/bin/env python

import argparse
from pandas import read_csv
from pandas import DataFrame
from matplotlib import pyplot as plt
import pandas as pd

def main(csv_file, put, runs, cut_off, step, out_file):
    # Read the results from CSV
    df = read_csv(csv_file)

    # Lists to store calculated mean and standard deviation data
    mean_list = []
    std_dev_list = []

    # Calculate mean and standard deviation for each time interval
    for subject in [put]:
        for fuzzer in ['aflnet', 'aflnet-tuples']:
            for cov_type in ['b_abs', 'b_per', 'l_abs', 'l_per']:
                # Get subject, fuzzer, and cov_type-specific DataFrame
                df1 = df[(df['subject'] == subject) & 
                         (df['fuzzer'] == fuzzer) & 
                         (df['cov_type'] == cov_type)]
                
                for time in range(1, cut_off + 1, step):
                    coverage_values = []

                    for run in range(1, runs + 1):
                        # Get data for this specific run
                        df2 = df1[df1['run'] == run]
                        
                        # Get the starting time for this run
                        start = df2.iloc[0, 0]
                        
                        # Filter rows up to the cutoff time for this run
                        df3 = df2[df2['time'] <= start + time * 60]
                        
                        # Append the last coverage value within this timeframe
                        coverage_values.append(df3.tail(1).iloc[0, 5])

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

    # Plot the data with shaded regions for standard deviation
    plt.figure(figsize=(12, 8))

    for (fuzzer, cov_type), group_df in merged_df.groupby(['fuzzer', 'cov_type']):
        # Plot the mean coverage line
        plt.plot(group_df['time'], group_df['mean_cov'], label=f"{fuzzer} - {cov_type}")
        
        # Add shaded area for standard deviation
        plt.fill_between(group_df['time'],
                         group_df['mean_cov'] - group_df['std_dev_cov'],
                         group_df['mean_cov'] + group_df['std_dev_cov'],
                         alpha=0.3)  # Adjust alpha for transparency of the shaded area

    # Label the plot
    plt.xlabel("Time (minutes)")
    plt.ylabel("Code Coverage")
    plt.title(f"Code Coverage Over Time for {put}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_file)
    plt.show()

# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()    
    parser.add_argument('-i','--csv_file',type=str,required=True,help="Full path to results.csv")
    parser.add_argument('-p','--put',type=str,required=True,help="Name of the subject program")
    parser.add_argument('-r','--runs',type=int,required=True,help="Number of runs in the experiment")
    parser.add_argument('-c','--cut_off',type=int,required=True,help="Cut-off time in minutes")
    parser.add_argument('-s','--step',type=int,required=True,help="Time step in minutes")
    parser.add_argument('-o','--out_file',type=str,required=True,help="Output file")

    args = parser.parse_args()
    main(args.csv_file, args.put, args.runs, args.cut_off, args.step, args.out_file)
