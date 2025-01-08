import argparse
import os
import tarfile
import pandas as pd
from matplotlib import pyplot as plt

def extract_phase_two_start(file_path):
    try:
        with tarfile.open(file_path, "r:gz") as tar:
            fuzzer_stats_file = [
                member for member in tar.getmembers() if "fuzzer_stats" in member.name
            ]
            if not fuzzer_stats_file:
                print(f"Warning: No fuzzer_stats found in {file_path}")
                return None

            fuzzer_stats = tar.extractfile(fuzzer_stats_file[0])
            if fuzzer_stats is None:
                print(f"Warning: Unable to extract fuzzer_stats from {file_path}")
                return None

            for line in fuzzer_stats:
                decoded_line = line.decode("utf-8").strip()
                if decoded_line.startswith("phase_two_start"):
                    return int(decoded_line.split(":")[1].strip())
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return None

def calculate_average_phase_two(target, fuzzer):
    phase_two_values = []
    for index in range(1, 9):
        file_name = f"out-{target}-{fuzzer}_{index}.tar.gz"
        if not os.path.exists(file_name):
            print(f"Warning: {file_name} is missing.")
            continue

        phase_two_start = extract_phase_two_start(file_name)
        if phase_two_start is not None:
            phase_two_values.append(phase_two_start)

    if phase_two_values:
        return sum(phase_two_values) / len(phase_two_values)
    return None

def main(csv_file, put, runs, cut_off, step, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    out_file = os.path.join(output_folder, "cov_over_time_with_phase_two.png")

    df = pd.read_csv(csv_file)
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.flatten()
    fig.suptitle(f"Code Coverage Over Time for {put}", fontsize=16)
    coverage_types = ['b_abs', 'b_per', 'l_abs', 'l_per']

    fuzzers = ['aflnet', 'aflnet-tuples', 'tuples-random', "tuples-delayed"]
    phase_two_averages = {}

    for fuzzer in fuzzers:
        phase_two_avg = calculate_average_phase_two(put, fuzzer)
        if phase_two_avg is not None:
            phase_two_averages[fuzzer] = phase_two_avg
            print(f"Average phase_two_start for {fuzzer}: {phase_two_avg}")

    for i, cov_type in enumerate(coverage_types):
        ax = axes[i]
        cov_type_df = df[df['cov_type'] == cov_type]

        for fuzzer, fuzzer_df in cov_type_df.groupby('fuzzer'):
            ax.plot(fuzzer_df['time'], fuzzer_df['mean_cov'], label=f"{fuzzer}")
            ax.fill_between(
                fuzzer_df['time'],
                fuzzer_df['mean_cov'] - fuzzer_df['std_dev_cov'],
                fuzzer_df['mean_cov'] + fuzzer_df['std_dev_cov'],
                alpha=0.3,
            )

            if fuzzer in phase_two_averages:
                ax.axvline(
                    x=phase_two_averages[fuzzer],
                    color="red",
                    linestyle="--",
                    label=f"{fuzzer} phase_two_start",
                )

        ax.set_xlabel("Time (minutes)")
        ax.set_ylabel("Coverage")
        ax.legend(loc="upper left")
        ax.grid(True)

    plt.tight_layout()
    plt.savefig(out_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--csv_file', type=str, required=True, help="Full path to results.csv")
    parser.add_argument('-p', '--put', type=str, required=True, help="Name of the subject program")
    parser.add_argument('-r', '--runs', type=int, required=True, help="Number of runs in the experiment")
    parser.add_argument('-c', '--cut_off', type=int, required=True, help="Cut-off time in minutes")
    parser.add_argument('-s', '--step', type=int, required=True, help="Time step in minutes")
    parser.add_argument('-o', '--output_folder', type=str, required=True, help="Output folder")

    args = parser.parse_args()
    main(args.csv_file, args.put, args.runs, args.cut_off, args.step, args.output_folder)
