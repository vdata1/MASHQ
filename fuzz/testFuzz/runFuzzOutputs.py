import os
import json
from collections import defaultdict
import re
import argparse

import subprocess
import threading
import logging

results = {}

# Default harness path, used unless --harness is passed on the command line.
DEFAULT_HARNESS = "../../harness/test262/combined_harness_test262.js"
# Other harnesses that have been used here in the past, kept for reference:
#   "../../harness/v8/harness.js"
#   "../../harness/webkit/ChakraCore"

# Run modes for --run-mode:
#   "matched"     (default) - each runtime runs its own test file: node tests on node,
#                 deno tests on deno, bun tests on bun.
#   "node-on-all" - the Node test file is harness-prepended exactly once (using Node's
#                 own harness style) and that SAME single file is then run, unmodified,
#                 on all three runtimes (node, deno, bun) - to see how Deno and Bun
#                 behave when handed a test written for Node, as-is.
RUN_MODE_MATCHED = "matched"
RUN_MODE_NODE_ON_ALL = "node-on-all"

HARNESS = DEFAULT_HARNESS  # overwritten in main() from parsed CLI args
BASEOUTPUTDIR = "./run_outputs"
PREPAREDDIR = "./prepared_outputs"  # harness-prepended copies live here, originals are never modified


def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

# Function to collect JS files by rounds and group them based on prefix
def get_js_files_by_rounds(base_dir):
    rounds_data = defaultdict(lambda: defaultdict(dict))  # {round_name: {prefix: {runtime: file_path}}}
    
    counter = 0
    rCounter = 0 
    # Traverse the base directory for rounds (round_1, round_2, etc.)
    for chunk in os.listdir(base_dir):
        chunkDir = os.path.join(base_dir, chunk)
        print("chunkDir: ", chunkDir)
        #tempList = []
        for round_dir in os.listdir(chunkDir):
            counter = 0
            
            print("round_dir: ", round_dir) 
            round_path = os.path.join(chunkDir, round_dir)
            print("round path: ", round_path)
            if os.path.isdir(round_path) and round_dir.startswith("round_"):
                # Traverse each runtime directory (node, deno, bun)
                #for runtime in ["node", "deno", "bun"]:
                    runtime_path = os.path.join(round_path, "node") #runtime)
                    if os.path.isdir(runtime_path):
                        for js_file in os.listdir(runtime_path):
                            #if js_file.endswith(".js"):
                            counter = counter + 3
                            print(round_path)
                            #print(os.path.join(os.path.join(round_path, "node"), js_file))
                            #print(tempList)
                            #if  js_file in tempList: 
                            #    print("repeated!", js_file)

                            #    rCounter = rCounter+1
                            # Extract the prefix before the first '_', or full name if no '_'
                            #file_prefix = js_file.split("_", 1)[0] if "_" in js_file else js_file[:-3]
                            #if round_dir in  rounds_data.keys() and js_file in rounds_data[round_dir].keys(): 
                            #    print("repeated!", js_file)
                            #else:      
                            rounds_data[round_dir][f'{chunk}_{js_file}']["node"] = os.path.join(os.path.join(round_path, "node"), js_file)
                            rounds_data[round_dir][f'{chunk}_{js_file}']["deno"] = os.path.join(os.path.join(round_path, "deno"), js_file)
                            rounds_data[round_dir][f'{chunk}_{js_file}']["bun"] = os.path.join(os.path.join(round_path, "bun"), js_file)
                            #tempList.append(js_file)

                            #print("\n \n \n Added to List: \n", rounds_data[round_dir][js_file]["node"], "\n", rounds_data[round_dir][js_file]["deno"], "\n", rounds_data[round_dir][js_file]["bun"], "\n")

            print(chunkDir, " : ", round_dir, " : ", counter)
            #print(len(tempList))
    #print("Total rCounter: ", rCounter)
    return rounds_data


def run_command(command, output_dict, key, timeout=1):
    try:
        print("Running: ", command)
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        output_dict[key] = result.stdout if result.returncode == 0 else result.stderr
        logging.info(f"{key} output for command {' '.join(command)}: {result.stdout}")
        print(f"{key} output for command {' '.join(command)}: {result.stdout}")
        if result.stderr:
            logging.error(f"{key} error for command {' '.join(command)}: {result.stderr}")
            print(f"{key} output for command {' '.join(command)}: {result.stdout}")
    except subprocess.TimeoutExpired:
        output_dict[key] = "Timeout"
        print(f"{key} output for command {' '.join(command)}: Timeout")
        logging.error(f"{key} command {' '.join(command)} timed out after {timeout} seconds")

# Function to process a single JavaScript file with all runtimes
def process_js_file(nodeTest, denoTest, bunTest, run_mode=RUN_MODE_MATCHED, timeout=10):
    #test_name = nodeTest.split("_node.js")[0]
    threads = []
    outputs = {"node": "", "deno": "", "bun": ""}

    # prepend_harness_and_imports no longer overwrites the original fuzz output;
    # it writes a harness-prepended copy under PREPAREDDIR and returns that path.
    if run_mode == RUN_MODE_NODE_ON_ALL:
        # Run the Node test file itself, unmodified/unadapted, on all three runtimes -
        # to see how Deno and Bun behave when handed a test written for Node, as-is.
        # We prepend the harness exactly once, using Node's own harness style (since
        # this is a Node test), and point every runtime at that SAME prepared file -
        # no per-runtime adaptation, no separate copies.
        node_prepared = prepend_harness_and_imports(nodeTest, HARNESS, "node")
        deno_prepared = node_prepared
        bun_prepared = node_prepared
    else:
        # Default "matched" behavior: each runtime runs its own corresponding test file.
        node_prepared = prepend_harness_and_imports(nodeTest, HARNESS, "node")
        deno_prepared = prepend_harness_and_imports(denoTest, HARNESS, "deno")
        bun_prepared = prepend_harness_and_imports(bunTest, HARNESS, "bun")


    commands = {
        "node": ["node", node_prepared],
        "deno": ["deno", "run", "-A", "-r", deno_prepared],
        "bun": ["bun", "run", bun_prepared]
    }
    
    # Create and start threads for each runtime
    for runtime in commands:
        thread = threading.Thread(target=run_command, args=(commands[runtime], outputs, runtime, timeout))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    

    return outputs

def run_js_file(runtimes, prefix, run_mode=RUN_MODE_MATCHED):

    result = process_js_file(runtimes["node"], runtimes["deno"], runtimes["bun"], run_mode=run_mode)
    print(f"Simulated result for {prefix} running {result}")  # Placeholder result
    return result

# Function to process the collected JS files, run them, and log the results
def process_and_run_files(base_dir, run_mode=RUN_MODE_MATCHED):
    grouped_files = get_js_files_by_rounds(base_dir)
    for index, key in grouped_files.items():
        print(index, ":", len(grouped_files[index])) 

    with open("./run_output_files.json", "w") as output: 
        json.dump(grouped_files, output, indent=4)
        print("grouped_files is written")
    # For each round and prefix, run the files for the different runtimes and log results
    
    for round_name, files_by_prefix in grouped_files.items(): # {round_name: {prefix: {runtime: file_path}}}
        counter = 0
        #print(round_name, "****")
        round_dir_output_path = os.path.join(BASEOUTPUTDIR, round_name)
        create_dir(round_dir_output_path)
        for prefix, runtimes in files_by_prefix.items():
            results = run_js_file(runtimes, prefix, run_mode=run_mode)
            counter = counter + 1 
            print("ROUND_NAME: ", round_name)
            # Log the results in a JSON file named after the prefix
            output_file_name = f'{round_name}_{prefix}_results_{counter}.json'
            print("FILENAME: ", output_file_name)
            output_file_path = os.path.join(round_dir_output_path, output_file_name)
            print("FILEPATH: ", output_file_path)
            with open(output_file_path, "w") as output_file:

                json.dump(results, output_file, indent=4)

            print(f"Results logged in {output_file_path}")


# Matches the *first* line of an import statement, e.g.:
#   import x from 'y';           import * as x from 'y';         import 'y';
#   import x, { a, b } from 'y'; import {                        (multi-line named imports)
_IMPORT_START_RE = re.compile(r'^\s*import\s')

# Matches the first line of a require-based declaration, e.g.:
#   const x = require('y');   let { a, b } = require('y')   var x = require('y')
_REQUIRE_START_RE = re.compile(r'^\s*(?:const|let|var)\b.*=\s*require\s*\(')

# Strips string-literal contents (single/double/backtick quoted) so bracket-counting
# below doesn't get confused by braces/parens that merely appear inside a string.
_STRING_LITERAL_RE = re.compile(r"""(['"`])(?:\\.|(?!\1).)*\1""", re.DOTALL)


def _bracket_balance(line):
    """Net change in {}/[]/() nesting depth contributed by this line, ignoring
    anything inside string literals."""
    stripped = _STRING_LITERAL_RE.sub('', line)
    opens = stripped.count('{') + stripped.count('[') + stripped.count('(')
    closes = stripped.count('}') + stripped.count(']') + stripped.count(')')
    return opens - closes


def extract_imports_and_requires(js_code_path):
    js_code = read_file(js_code_path)

    import_statements = []
    lines = js_code.split('\n')
    new_code_lines = []

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        if _IMPORT_START_RE.match(line) or _REQUIRE_START_RE.match(line):
            # Accumulate lines until any opened brackets/braces/parens on the
            # statement are balanced again (handles multi-line named imports /
            # destructured requires), then also swallow a trailing ';' if the
            # statement is terminated with one (many fuzzed files omit it, so
            # this is optional rather than required).
            statement_lines = [line]
            balance = _bracket_balance(line)
            j = i
            while balance > 0 and j + 1 < n:
                j += 1
                statement_lines.append(lines[j])
                balance += _bracket_balance(lines[j])

            # If the statement ended without a semicolon on its own line but the
            # next line starts one right after (e.g. `require('y')\n;`), pull it in.
            if j + 1 < n and lines[j + 1].lstrip().startswith(';') and not statement_lines[-1].rstrip().endswith(';'):
                j += 1
                statement_lines.append(lines[j])

            import_statements.append('\n'.join(statement_lines))
            i = j + 1
        else:
            new_code_lines.append(line)
            i += 1

    return '\n'.join(new_code_lines), import_statements

def prepend_harness_and_imports(js_code, harness_code, runtime):
    """
    Reads the original fuzz-output file at `js_code` and the harness, and writes a
    harness-prepended copy to a mirrored path under PREPAREDDIR. The original file at
    `js_code` is never modified. Returns the path to the newly written, runnable file.
    """
    js_code_without_imports, js_imports = extract_imports_and_requires(js_code)
    harness_code_without_imports, harness_imports = extract_imports_and_requires(harness_code)
    
    all_imports = list(dict.fromkeys(js_imports + harness_imports))  
    
    #commented to replace it with import the harness code in the js_code
    #final_code = '\n'.join(all_imports) + '\n\n' + '/********Sart of Harness********/' + '\n\n' + harness_code_without_imports + '\n\n' + '/********End of Harness********/' + '\n\n' + js_code_without_imports



    if runtime == "node" or runtime == "bun": 
        final_code = '\n'.join(all_imports) + '\n\n' + '/********Sart of Harness********/' + '\n\n' + "var assert = require('assert');" + '\n\n' + harness_code_without_imports + '\n\n' + '/********End of Harness********/' + '\n\n' + js_code_without_imports
    elif runtime == "deno":
        final_code = '\n'.join(all_imports) + '\n\n' + '/********Sart of Harness********/' + '\n\n' + "import * as assert from 'assert';" + '\n\n' + harness_code_without_imports + '\n\n' + '/********End of Harness********/' + '\n\n' + js_code_without_imports    

    # Mirror the original relative path under PREPAREDDIR instead of overwriting js_code in place.
    rel_path = os.path.relpath(js_code, start=".")
    # Guard against paths that fall outside the current tree (e.g. absolute paths or ../ escapes)
    # by stripping any leading ".." segments so everything still lands under PREPAREDDIR.
    rel_path_parts = [p for p in rel_path.split(os.sep) if p not in ("..", "")]

    # Always tag the prepared filename with the runtime it was prepared for. This matters
    # most in RUN_MODE_NODE_ON_ALL, where the *same* source file (the Node test) is prepared
    # three times, once per runtime - without this, each prepend call would overwrite the
    # previous runtime's prepared copy at the same mirrored path.
    file_name = rel_path_parts[-1] if rel_path_parts else os.path.basename(js_code)
    base_name, ext = os.path.splitext(file_name)
    prepared_file_name = f"{base_name}.{runtime}{ext or '.js'}"
    out_path = os.path.join(PREPAREDDIR, *rel_path_parts[:-1], prepared_file_name)

    create_dir(os.path.dirname(out_path))
    write_file(out_path, final_code)

    return out_path

def create_dir(dir):
    if not os.path.exists(dir):
            os.makedirs(dir)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run fuzz-generated JS test files across Node, Deno, and Bun."
    )
    parser.add_argument(
        "--harness",
        dest="harness",
        default=DEFAULT_HARNESS,
        help=(
            "Path to the harness JS file to prepend to each test file before running it. "
            f"Defaults to the test262 combined harness ({DEFAULT_HARNESS})."
        ),
    )
    parser.add_argument(
        "--run-mode",
        dest="run_mode",
        choices=[RUN_MODE_MATCHED, RUN_MODE_NODE_ON_ALL],
        default=RUN_MODE_MATCHED,
        help=(
            f"'{RUN_MODE_MATCHED}' (default): run each runtime's own test file on that runtime "
            "(node tests on node, deno tests on deno, bun tests on bun). "
            f"'{RUN_MODE_NODE_ON_ALL}': harness-prepend the Node test file exactly once, then run "
            "that same unmodified file on all three runtimes (node, deno, bun), to see how Deno "
            "and Bun behave when given a Node test as-is."
        ),
    )
    return parser.parse_args()


# Main function to handle execution
def main(args):
    base_dir = "./output"  # Change this to fuzz outputs
    process_and_run_files(base_dir, run_mode=args.run_mode)

if __name__ == "__main__":
    args = parse_args()
    HARNESS = args.harness

    create_dir(BASEOUTPUTDIR)
    create_dir(PREPAREDDIR)
    print("start running")
    print(f"harness: {HARNESS}")
    print(f"run mode: {args.run_mode}")
    main(args)
    print("done")