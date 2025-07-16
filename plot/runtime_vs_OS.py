import matplotlib.pyplot as plt
from collections import defaultdict
import os
import json
import numpy as np
from matplotlib.ticker import MultipleLocator, AutoMinorLocator


def extract_round_num(filename):
    # Extract round number from filename (assuming format: ..._roundNUMBER_...)
    # Adjust this function if your filename format is different
    parts = filename.split("_")
    if "low" in parts and "level" in parts:
        n = int(parts[parts.index("round") + 1])
        return n

def get_dir_label(directory):
    if "test262X15.latest.linux" in directory:
        return "test262 (Linux)"
    elif "v8.500x15.latest.linux" in directory:
        return "v8 (Linux)"
    elif "v8.500X16.latest.windows" in directory:
        return "v8 (Windows)"
    elif "test262.500X15.latest.windows" in directory:
        return "test262 (Windows)"
    else:
        return os.path.basename(directory)

plt.figure(figsize=(16, 10))

# Define line styles for plotting
line_styles = ['-', '--', '-.', ':']

# Define the list of directories to process
directories = [
     "/Users/vdata/Desktop/CISPA_projects/node-deno-bun/fuzz/testFuzz/test262X15.latest.linux/filtered/frequency",
     "/Users/vdata/Desktop/CISPA_projects/node-deno-bun/fuzz/testFuzz/v8.500x15.latest.linux/filtered/frequency",
     "/Users/vdata/Desktop/CISPA_projects/node-deno-bun/fuzz/testFuzz/windows/v8.500X16.latest.windows/filtered/frequency",
     "/Users/vdata/Desktop/CISPA_projects/node-deno-bun/fuzz/testFuzz/windows/test262.500X15.latest.windows/filtered/frequency"
]

for idx, directory in enumerate(directories):
    dir_label = get_dir_label(directory)
    filter_sums = defaultdict(int)
    for filename in os.listdir(directory):
        if "low_level" in filename and filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as f:
                data = json.load(f)
                for filter_name, count in data.items():
                    filter_sums[filter_name] += count

    # Top 5 filters
    top_5 = sorted(filter_sums.items(), key=lambda x: x[1], reverse=True)[:3]
    filter_counts_per_round = {filter_name: [] for filter_name, _ in top_5}
    round_numbers = []

    
    # Sort files by round number
    sorted_files = sorted(
        [f for f in os.listdir(directory) if "low_level" in f and f.endswith(".json")],
        key=extract_round_num
    )

    for filename in sorted_files:
        round_num = extract_round_num(filename)
        if round_num is None or round_num > 16:  # Skip if round number is None or greater than 17
            continue
        round_numbers.append(round_num)
        filepath = os.path.join(directory, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
            for filter_name in filter_counts_per_round:
                count = data.get(filter_name, 0)
                filter_counts_per_round[filter_name].append(count)
    # Find top 2 filters in rounds 14 to 17 for this directory, excluding those already in the plot
    plotted_filters = set(filter_counts_per_round.keys())
    extra_filters = set()
    extra_filter_counts = defaultdict(lambda: [0] * len(round_numbers))

    for round_num in range(14, 18):
        round_file = next(
            (f for f in os.listdir(directory) if "low_level" in f and f.endswith(".json") and extract_round_num(f) == round_num),
            None
        )
        if round_file:
            filepath = os.path.join(directory, round_file)
            with open(filepath, "r") as f:
                data = json.load(f)
                # Exclude filters already in the plot
                filtered_items = [(k, v) for k, v in data.items() if k not in plotted_filters]
                top_2 = sorted(filtered_items, key=lambda x: x[1], reverse=True)[:2]
                print(f"Top 2 (not in plot) filters in round {round_num} for {dir_label}:")
                for filter_name, count in top_2:
                    print(f"  {filter_name}: {count}")
                    extra_filters.add(filter_name)
                    # Fill the count for this round in the extra_filter_counts
                    if round_num in round_numbers:
                        idx_round = round_numbers.index(round_num)
                        extra_filter_counts[filter_name][idx_round] = count
        else:
            print(f"No round {round_num} file found for {dir_label}")

    # Plot lines for these extra filters (only for rounds 14-17, zeros elsewhere)
    for i, filter_name in enumerate(extra_filters):
        plt.plot(
            round_numbers,
            extra_filter_counts[filter_name],
            label=f"{dir_label}: {filter_name} (extra)",
            linestyle='dotted',
            linewidth=2,
            color=f"C{(idx+1+i)%10}"
        )
        
    print(round_numbers)

    # Plot for each filter in this directory
    for filter_name, counts in filter_counts_per_round.items():
        plt.plot(
            round_numbers,
            counts,
            label=f"{dir_label}: {filter_name}",
            linestyle=line_styles[idx % len(line_styles)]
        )
plt.xlabel(r"$\bf{Round\ Number}$", fontsize=18)
plt.ylabel(r"$\bf{Count}$", fontsize=18)
plt.xticks(
    ticks=np.arange(min(round_numbers), max(round_numbers) + 1, 1),
    fontsize=16,
    fontweight='bold'
)

# Add minor yticks between major yticks, with smaller, not bold font
plt.gca().yaxis.set_minor_locator(AutoMinorLocator(2))
plt.tick_params(axis='y', which='minor', labelsize=14, labelcolor='black', right=True)
for label in plt.gca().get_yticklabels(minor=True):
    label.set_fontweight('normal')


plt.yticks(fontsize=16, fontweight='bold')
plt.legend(loc="upper right", fontsize="medium", ncol=2, title_fontproperties={"weight": "bold"})
plt.tight_layout()
#plt.title("Top 5 Filters: Count per Round")
#plt.show()

# --- Plot: Top 5 filters per OS group (Linux vs Windows), using same colors for same filters ---

plt.figure(figsize=(16, 10))

os_groups = {
    "Linux": [directories[0], directories[1]],
    "Windows": [directories[2], directories[3]],
}
os_styles = {
    "Linux": "-",
    "Windows": "--"
}

# 1. Find the union of top 5 filters across both OS groups (by total count)
filter_sums_all = defaultdict(int)
for dirs in os_groups.values():
    for directory in dirs:
        for filename in os.listdir(directory):
            if "low_level" in filename and filename.endswith(".json"):
                filepath = os.path.join(directory, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)
                    for filter_name, count in data.items():
                        filter_sums_all[filter_name] += count
top_filters = sorted(filter_sums_all.items(), key=lambda x: x[1], reverse=True)[:5]
top_filter_names = [f for f, _ in top_filters]
color_map = {filter_name: f"C{i}" for i, filter_name in enumerate(top_filter_names)}

for os_idx, (os_name, dirs) in enumerate(os_groups.items()):
    # For each filter, collect counts per round (sum across dirs in group)
    filter_counts_per_round = {filter_name: [] for filter_name in top_filter_names}
    round_numbers = []
    for round_num in range(1, 17):
        round_numbers.append(round_num)
        for filter_name in top_filter_names:
            total = 0
            for directory in dirs:
                round_file = next(
                    (f for f in os.listdir(directory)
                     if "low_level" in f and f.endswith(".json") and extract_round_num(f) == round_num),
                    None
                )
                if round_file:
                    filepath = os.path.join(directory, round_file)
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        total += data.get(filter_name, 0)
            filter_counts_per_round[filter_name].append(total)

    # Plot for each filter in this OS group
    for i, (filter_name, counts) in enumerate(filter_counts_per_round.items()):
        plt.plot(
            round_numbers,
            counts,
            label=f"{os_name}: {filter_name}",
            linestyle=os_styles[os_name],
            linewidth=4,
            color=color_map[filter_name]
        )

plt.xlabel(r"$\bf{Round\ Number}$", fontsize=28)
plt.ylabel(r"$\bf{Filters\ Count}$", fontsize=28)
plt.xticks(
    ticks=np.arange(min(round_numbers), max(round_numbers) + 1, 1),
    fontsize=27,
    fontweight='bold'
)
plt.yticks(fontsize=27, fontweight='bold')
plt.legend(
    loc="upper right",
    #bbox_to_anchor=(1.02, 1),
    fontsize=15,
    ncol=2,
    title_fontproperties={"weight": "bold", "size": 15},
    prop={"weight": "bold", "size": 15},
    #borderaxespad=0.
)
plt.tight_layout()
#plt.title("Top 5 Filters per OS Group: Linux (solid), Windows (dashed)", fontsize=18)
plt.show()


'''
# This script processes JSON files from specified directories, extracts filter counts, and plots the results.
# --- Cumulative plot for the same filters ---

plt.figure(figsize=(16, 10))
for idx, directory in enumerate(directories):
    dir_label = get_dir_label(directory)
    filter_sums = defaultdict(int)
    for filename in os.listdir(directory):
        if "low_level" in filename and filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as f:
                data = json.load(f)
                for filter_name, count in data.items():
                    filter_sums[filter_name] += count

    # Top 5 filters
    top_5 = sorted(filter_sums.items(), key=lambda x: x[1], reverse=True)[:5]
    filter_counts_per_round = {filter_name: [] for filter_name, _ in top_5}
    round_numbers = []

    # Sort files by round number
    sorted_files = sorted(
        [f for f in os.listdir(directory) if "low_level" in f and f.endswith(".json")],
        key=extract_round_num
    )

    for filename in sorted_files:
        round_num = extract_round_num(filename)
        if round_num is None or round_num > 17:
            continue
        round_numbers.append(round_num)
        filepath = os.path.join(directory, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
            for filter_name in filter_counts_per_round:
                count = data.get(filter_name, 0)
                filter_counts_per_round[filter_name].append(count)

    # Plot cumulative sum for each filter in this directory
    for filter_name, counts in filter_counts_per_round.items():
        cumulative_counts = np.cumsum(counts)
        plt.plot(
            round_numbers,
            cumulative_counts,
            label=f"{dir_label}: {filter_name}",
            linestyle=line_styles[idx % len(line_styles)]
        )
plt.xlabel("Round Number")
plt.ylabel("Cumulative Count")
plt.legend(loc="upper left", fontsize="small", ncol=2)
plt.tight_layout()
plt.title("Top 5 Filters: Cumulative Count per Round")
plt.show()


# --- Cumulative plot for test262 (Linux and Windows) ---

plt.figure(figsize=(16, 10))
test262_dirs = [
    directories[0],  # test262 (Linux)
    directories[3],  # test262 (Windows)
]
for idx, directory in enumerate(test262_dirs):
    dir_label = get_dir_label(directory)
    filter_sums = defaultdict(int)
    for filename in os.listdir(directory):
        if "low_level" in filename and filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as f:
                data = json.load(f)
                for filter_name, count in data.items():
                    filter_sums[filter_name] += count

    # Top 5 filters
    top_5 = sorted(filter_sums.items(), key=lambda x: x[1], reverse=True)[:10]
    filter_counts_per_round = {filter_name: [] for filter_name, _ in top_5}
    round_numbers = []

    sorted_files = sorted(
        [f for f in os.listdir(directory) if "low_level" in f and f.endswith(".json")],
        key=extract_round_num
    )

    for filename in sorted_files:
        round_num = extract_round_num(filename)
        if round_num is None or round_num > 17:
            continue
        round_numbers.append(round_num)
        filepath = os.path.join(directory, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
            for filter_name in filter_counts_per_round:
                count = data.get(filter_name, 0)
                filter_counts_per_round[filter_name].append(count)

    for filter_name, counts in filter_counts_per_round.items():
        cumulative_counts = np.cumsum(counts)
        plt.plot(
            round_numbers,
            cumulative_counts,
            label=f"{dir_label}: {filter_name}",
            linestyle=line_styles[idx % len(line_styles)]
        )
plt.xlabel("Round Number")
plt.ylabel("Cumulative Count")
plt.legend(loc="upper left", fontsize="small", ncol=2)
plt.tight_layout()
plt.title("Test262 (Linux & Windows): Top 5 Filters Cumulative Count per Round")
plt.show()

# --- Cumulative plot for v8 (Linux and Windows) ---

plt.figure(figsize=(16, 10))
v8_dirs = [
    directories[1],  # v8 (Linux)
    directories[2],  # v8 (Windows)
]
for idx, directory in enumerate(v8_dirs):
    dir_label = get_dir_label(directory)
    filter_sums = defaultdict(int)
    for filename in os.listdir(directory):
        if "low_level" in filename and filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as f:
                data = json.load(f)
                for filter_name, count in data.items():
                    filter_sums[filter_name] += count

    # Top 5 filters
    top_5 = sorted(filter_sums.items(), key=lambda x: x[1], reverse=True)[:10]
    filter_counts_per_round = {filter_name: [] for filter_name, _ in top_5}
    round_numbers = []

    sorted_files = sorted(
        [f for f in os.listdir(directory) if "low_level" in f and f.endswith(".json")],
        key=extract_round_num
    )

    for filename in sorted_files:
        round_num = extract_round_num(filename)
        if round_num is None or round_num > 17:
            continue
        round_numbers.append(round_num)
        filepath = os.path.join(directory, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
            for filter_name in filter_counts_per_round:
                count = data.get(filter_name, 0)
                filter_counts_per_round[filter_name].append(count)

    for filter_name, counts in filter_counts_per_round.items():
        cumulative_counts = np.cumsum(counts)
        plt.plot(
            round_numbers,
            cumulative_counts,
            label=f"{dir_label}: {filter_name}",
            linestyle=line_styles[idx % len(line_styles)]
        )
plt.xlabel("Round Number")
plt.ylabel("Cumulative Count")
plt.legend(loc="upper left", fontsize="small", ncol=2)
plt.tight_layout()
plt.title("V8 (Linux & Windows): Top 5 Filters Cumulative Count per Round")
plt.show()

# Find top 15 common filters across all directories, based on the highest value in any directory
filter_max_in_dir = defaultdict(lambda: defaultdict(int))
filter_presence = defaultdict(set)

# Collect max value for each filter in each directory and track presence
for idx, directory in enumerate(directories):
    for filename in os.listdir(directory):
        if "low_level" in filename and filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as f:
                data = json.load(f)
                for filter_name, count in data.items():
                    filter_max_in_dir[filter_name][directory] = max(
                        filter_max_in_dir[filter_name][directory], count
                    )
                    filter_presence[filter_name].add(directory)

# Only keep filters present in all directories
common_filters = [f for f, dirs in filter_presence.items() if len(dirs) == len(directories)]

# For each filter, get the highest value across all directories
filter_highest = {
    f: max(filter_max_in_dir[f].values()) for f in common_filters
}

# Get top 15 filters by highest value across all dirs
top_15_common = sorted(
    filter_highest.items(),
    key=lambda x: x[1], reverse=True
)[:3]
top_15_names = [f for f, _ in top_15_common]

plt.figure(figsize=(16, 10))

for idx, directory in enumerate(directories):
    dir_label = get_dir_label(directory)
    filter_counts_per_round = {filter_name: [] for filter_name in top_15_names}
    round_numbers = []

    sorted_files = sorted(
        [f for f in os.listdir(directory) if "low_level" in f and f.endswith(".json")],
        key=extract_round_num
    )

    for filename in sorted_files:
        round_num = extract_round_num(filename)
        if round_num is None or round_num > 17:
            continue
        round_numbers.append(round_num)
        filepath = os.path.join(directory, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
            for filter_name in filter_counts_per_round:
                count = data.get(filter_name, 0)
                filter_counts_per_round[filter_name].append(count)

    for filter_name, counts in filter_counts_per_round.items():
        cumulative_counts = np.cumsum(counts)
        plt.plot(
            round_numbers,
            cumulative_counts,
            label=f"{dir_label}: {filter_name}",
            linestyle=line_styles[idx % len(line_styles)]
        )

plt.xlabel("Round Number")
plt.ylabel("Cumulative Count")
plt.legend(loc="upper left", fontsize="small", ncol=2)
plt.tight_layout()
#plt.title("Top 15 Common Filters (by Max Value in Any Dir): Cumulative Count per Round")
plt.show()

'''