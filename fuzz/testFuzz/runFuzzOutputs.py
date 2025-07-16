import os
import json
from collections import defaultdict
import re

import subprocess
import threading
import logging

results = {}
HARNESS = "../../harness/v8/harness.js" #"../../harness/test262/combined_harness_test262.js" #"../../harness/v8/harness.js" #"../../harness/webkit/ChakraCore" #"../../harness/test262/combined_harness_test262.js" #"../../harness/v8/harness.js"
BASEOUTPUTDIR = "./run_outputs"


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
def process_js_file(nodeTest, denoTest, bunTest, timeout=10):
    #test_name = nodeTest.split("_node.js")[0]
    threads = []
    outputs = {"node": "", "deno": "", "bun": ""}
    
    prepend_harness_and_imports(nodeTest, HARNESS)
    prepend_harness_and_imports(denoTest, HARNESS)
    prepend_harness_and_imports(bunTest, HARNESS)


    commands = {
        "node": ["node", nodeTest],
        "deno": ["deno", "run", "-A", "-r", denoTest],
        "bun": ["bun", "run", bunTest]
    }
    
    # Create and start threads for each runtime
    for runtime in commands:
        thread = threading.Thread(target=run_command, args=(commands[runtime], outputs, runtime, timeout))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    

    return outputs

def run_js_file(runtimes, prefix):

    result = process_js_file(runtimes["node"], runtimes["deno"], runtimes["bun"])
    print(f"Simulated result for {prefix} running {result}")  # Placeholder result
    return result

# Function to process the collected JS files, run them, and log the results
def process_and_run_files(base_dir):
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
            results = run_js_file(runtimes, prefix)
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


def extract_imports_and_requires(js_code_path):
    js_code = read_file(js_code_path)

    import_statements = []
    
    import_regex = r'^\s*(import\s.*?;\s*)'
    require_regex = r'^\s*(const\s.*?=\s*require\(.*?\);\s*)'
    
    lines = js_code.split('\n')
    new_code_lines = []
    
    for line in lines:
        import_match = re.match(import_regex, line)
        require_match = re.match(require_regex, line)
        
        if import_match:
            import_statements.append(import_match.group(1))
        elif require_match:
            import_statements.append(require_match.group(1))
        else:
            new_code_lines.append(line)
    
    return '\n'.join(new_code_lines), import_statements

def prepend_harness_and_imports(js_code, harness_code):
    js_code_without_imports, js_imports = extract_imports_and_requires(js_code)
    harness_code_without_imports, harness_imports = extract_imports_and_requires(harness_code)
    
    all_imports = list(dict.fromkeys(js_imports + harness_imports))  
    
    final_code = '\n'.join(all_imports) + '\n\n' + '/********Sart of Harness********/' + '\n\n' + harness_code_without_imports + '\n\n' + '/********End of Harness********/' + '\n\n' + js_code_without_imports
    write_file(js_code, final_code)

def create_dir(dir):
    if not os.path.exists(dir):
            os.makedirs(dir)


# Main function to handle execution
def main():
    base_dir = "./output"  # Change this to fuzz outputs
    process_and_run_files(base_dir)

if __name__ == "__main__":
    create_dir(BASEOUTPUTDIR)
    print("start running")
    main()
    print("done")



