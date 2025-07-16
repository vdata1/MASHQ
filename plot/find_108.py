import json
import os
import re
import sys

def normalize_filename(filename):
    # Remove '_results_[number]' from filename
    return re.sub(r'_results_\d+', '', filename)

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def main(json1_path, json2_path):
    data1 = load_json(json1_path)
    data2 = load_json(json2_path)

    keys1 = set(data1.keys())
    keys2 = set(data2.keys())

    norm_keys1 = {normalize_filename(k): k for k in keys1}
    norm_keys2 = {normalize_filename(k): k for k in keys2}

    unmatched1 = [norm_keys1[k] for k in norm_keys1 if k not in norm_keys2]
    unmatched2 = [norm_keys2[k] for k in norm_keys2 if k not in norm_keys1]

    if unmatched1:
        print(f"Files in {os.path.dirname(json1_path)} not matched in {os.path.dirname(json2_path)}:")
        for f in unmatched1:
            print(f)
    if unmatched2:
        print(f"Files in {os.path.dirname(json2_path)} not matched in {os.path.dirname(json1_path)}:")
        for f in unmatched2:
            print(f)
    if not unmatched1 and not unmatched2:
        print("All files matched.")

    # Find files where deno has syntaxError in one, but not in the other
    print("\nFiles where 'deno' has syntaxError in one file but not in the other:")
    for norm_key in set(norm_keys1.keys()) & set(norm_keys2.keys()):
        k1 = norm_keys1[norm_key]
        k2 = norm_keys2[norm_key]
        v1 = data1[k1]
        v2 = data2[k2]
        # Check if both have 'deno' key
        if 'deno' in v1 and 'deno' in v2:
            deno1 = v1['deno']
            deno2 = v2['deno']
            err1 = isinstance(deno1, str) and "SyntaxError" in deno1
            err2 = isinstance(deno2, str) and "SyntaxError" in deno2
            if err1 and not err2:
                print(f"{k1} in {os.path.dirname(json1_path)} has syntaxError, but {k2} in {os.path.dirname(json2_path)} does not.")
            elif err2 and not err1:
                print(f"{k2} in {os.path.dirname(json2_path)} has syntaxError, but {k1} in {os.path.dirname(json1_path)} does not.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python find_108.py <json_file1> <json_file2>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])