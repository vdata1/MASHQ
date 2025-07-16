import os
import json
from collections import defaultdict
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# Directory containing the JSON files
directory = "/Users/vdata/Desktop/CISPA_projects/node-deno-bun/fuzz/testFuzz/test262X15.latest.linux/filtered/frequency"
            #"/Users/vdata/Desktop/CISPA_projects/node-deno-bun/fuzz/testFuzz/v8.500x15.latest.linux/filtered/frequency"
            #"/Users/vdata/Desktop/CISPA_projects/node-deno-bun/fuzz/testFuzz/windows/v8.500X16.latest.windows/filtered/frequency" 
            #"/Users/vdata/Desktop/CISPA_projects/node-deno-bun/fuzz/testFuzz/windows/test262.500X15.latest.windows/filtered/frequency" 

# Dictionary to hold the sum for each filter
filter_sums = defaultdict(int)

# Iterate over all files in the directory
for filename in os.listdir(directory):
    if "low_level" in filename and filename.endswith(".json"):
        filepath = os.path.join(directory, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
            # Assuming data is a dict of {filter_name: count}
            for filter_name, count in data.items():
                filter_sums[filter_name] += count

# Print the sum for each filter
#for filter_name, total in filter_sums.items():
#    print(f"{filter_name}: {total}")

# Print the top 11 filters by total count
print("\nTop 11 filters:")
top_11 = sorted(filter_sums.items(), key=lambda x: x[1], reverse=True)[:5]
print("\n".join(f"{filter_name}: {total}" for filter_name, total in top_11))

# Find the first round each top filter appeared in
filter_first_round = {filter_name: None for filter_name, _ in top_11}

# Iterate over all files again to find first appearance
def extract_round_num(filename):
    # Extract round number from filename (assuming format: ..._roundNUMBER_...)
    # Adjust this function if your filename format is different
    parts = filename.split("_")
    if "low" in parts and "level" in parts:
        n = int(parts[parts.index("round") + 1])
        return n

# Sort files by extracted round number
sorted_files = sorted(
    [f for f in os.listdir(directory) if "low_level" in f and f.endswith(".json")],
    key=extract_round_num
)

for filename in sorted_files:
    # Extract round number from filename
    round_num = extract_round_num(filename)
    filepath = os.path.join(directory, filename)
    with open(filepath, "r") as f:
        data = json.load(f)
        for filter_name in filter_first_round:
            if filter_first_round[filter_name] is None and filter_name in data:
                filter_first_round[filter_name] = round_num

print("\nFirst appearance round for top 11 filters:")
for filter_name, round_num in filter_first_round.items():
    print(f"{filter_name}: round {round_num if round_num is not None else 'N/A'}")



    import matplotlib.pyplot as plt

    # Prepare data: for each top filter, collect counts per round
    filter_counts_per_round = {filter_name: [] for filter_name, _ in top_11}
    round_numbers = []

    for filename in sorted_files:
        round_num = extract_round_num(filename)
        round_numbers.append(round_num)
        filepath = os.path.join(directory, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
            for filter_name in filter_counts_per_round:
                count = data.get(filter_name, 0)
                filter_counts_per_round[filter_name].append(count)

# Plot
plt.figure(figsize=(16, 10))
for filter_name, counts in filter_counts_per_round.items():
    plt.plot(round_numbers, counts, label=filter_name)

plt.xlabel("Round Number")
plt.ylabel("Count per Round")
#plt.title("Top 25 Filters: Count per Round")
plt.legend(loc="upper right", fontsize="small", ncol=2)
plt.tight_layout()
plt.show()


# Plot cumulative counts for each top filter
plt.figure(figsize=(16, 10))
for filter_name, counts in filter_counts_per_round.items():
    cumulative_counts = []
    total = 0
    for c in counts:
        total += c
        cumulative_counts.append(total)
    plt.plot(round_numbers, cumulative_counts, label=filter_name)

plt.xlabel("Round Number")
plt.ylabel("Cumulative Count")
plt.legend(loc="upper left", fontsize="small", ncol=2)
plt.tight_layout()
plt.title("Top 25 Filters: Cumulative Count per Round")
plt.show()


# Prepare data for 3D plot
# For each round, sum counts for top 25 filters in low_level and other files

# Get all relevant files and their round numbers
all_files = [
    f for f in os.listdir(directory)
    if f.endswith(".json") and extract_round_num(f) is not None
]
all_files_sorted = sorted(all_files, key=extract_round_num)
all_rounds = sorted(set(extract_round_num(f) for f in all_files_sorted))

# For each round, sum counts for top 25 filters in low_level and other files
low_level_counts = []
other_counts = []
for round_num in all_rounds:
    low_level_sum = 0
    other_sum = 0
    # Find files for this round
    for f in all_files_sorted:
        if extract_round_num(f) == round_num:
            filepath = os.path.join(directory, f)
            with open(filepath, "r") as file:
                data = json.load(file)
                for filter_name, _ in top_11:
                    count = data.get(filter_name, 0)
                    if "low_level" in f:
                        low_level_sum += count
                    else:
                        other_sum += count
    low_level_counts.append(low_level_sum)
    other_counts.append(other_sum)

# Prepare meshgrid for 3D plot
X = np.array(low_level_counts)
Y = np.array(all_rounds)
Z = np.array(other_counts)

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

ax.plot(X, Y, Z, marker='o')
ax.set_xlabel('Low-level filter results (sum of top 25)')
ax.set_ylabel('Round Number')
ax.set_zlabel('Other filter results (sum of top 25)')
ax.set_title('3D Plot: Top 25 Filters (Low-level vs Other) per Round')

plt.tight_layout()
plt.show()