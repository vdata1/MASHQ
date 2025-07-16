import os
import json
import re
from collections import defaultdict

def extract_round_number(filename):
    match = re.search(r'round_(\d+)', filename)
    return int(match.group(1)) if match else None

def is_filter_file(filename):
    return filename.endswith('_filter_count.json') and 'low_level' not in filename

def is_low_level_filter_file(filename):
    return filename.endswith('_low_level_filter_count.json')

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def sum_values(d):
    return sum(d.values())

def process_directory(directory_path):
    files = os.listdir(directory_path)
    round_pairs = defaultdict(dict)

    for filename in files:
        round_num = extract_round_number(filename)
        if round_num is None:
            continue

        if is_filter_file(filename):
            round_pairs[round_num]['filter'] = filename
        elif is_low_level_filter_file(filename):
            round_pairs[round_num]['low_level'] = filename

    for round_num, pair in sorted(round_pairs.items()):
        if 'filter' in pair and 'low_level' in pair:
            filter_path = os.path.join(directory_path, pair['filter'])
            low_level_path = os.path.join(directory_path, pair['low_level'])

            filter_data = load_json(filter_path)
            low_level_data = load_json(low_level_path)

            total_sum = sum_values(filter_data) + sum_values(low_level_data)
            print(f"Round {round_num}: Total Sum = {total_sum}")
        else:
            print(f"Round {round_num}: Missing one of the pair files")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory_path>")
    else:
        process_directory(sys.argv[1])
