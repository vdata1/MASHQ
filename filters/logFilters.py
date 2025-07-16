from collections import OrderedDict
import spacy
from nltk.corpus import stopwords

import os
import json
import shutil 

import re 

nlp = spacy.load("en_core_web_md")
stop_words = set(stopwords.words("english"))
#nlp.max_length = 2000000 #newly added - can parse upto 2million characters now, default was 1million

cwd = os.getcwd()

#collector
base_directory = os.path.join(cwd,"run_outputs")
output_file = os.path.join(cwd,"fuzzResults.json")


#filter
source_filter = os.path.join(cwd,"separated",'differror.json')
destination_folder = os.path.join(cwd,'filtered_op.json')
remaining_folder = os.path.join(cwd,"remaining.json")
filtered = os.path.join(cwd,"filtered")
os.makedirs(filtered, exist_ok=True)
    

#separator
source_separator = os.path.join(cwd,"fuzzResults.json")
panic_file = os.path.join(cwd,"separated","panic.json") 
timeout_file = os.path.join(cwd,"separated","timeout.json")
same_error_file = os.path.join(cwd,"separated","same_error.json")
sameoutput_file = os.path.join(cwd,"separated","sameoutput.json")
dynamic_file = os.path.join(cwd,"separated","dynamic_samerror.json")
diff_error_file = os.path.join(cwd,"separated","differror.json")

keywords = ["ReferenceError:", "TypeError:", "SyntaxError:", "Test262Error","RangeError:"]

panic_flag = False 
timeout_flag = False 
same_error_flag = False 
sameoutput_flag = False 

def repeat_checker(statement):
    lines = [line.strip() for line in statement.split('\n') if line.strip()]
    if not lines:
        print("Edge case 1")
        return ""
    first_line = lines[0]
    if all(line == first_line for line in lines):
        print("Million detected 1")
        return first_line
    else:
        first_index = statement.find(first_line)
        second_index = statement.find(first_line,first_index+1)

        return_str = ""
        if second_index != 0:
            for i in range(0,second_index):
                return_str += statement[i]

        if return_str != "":
            print("Million detected 2")
        else:
            print("Edge case 2")

        return return_str

def error_similarity(statement1, statement2):
    
    if not statement1 or not statement2:
        return 0 
    elif (statement1=="" and statement2!="") or (statement2=="" and statement1!=""):
        return 0
    elif statement1 == statement2 or (statement1=="" and statement2==""):
        return 100
    else:

        if len(statement1)>1000000:
            #print("More than a million")
            statement1 = repeat_checker(statement1)
            if statement1 == "":
                return 0
        if len(statement2)>1000000:
            #print("More than a million")
            statement2 = repeat_checker(statement2)
            if statement2 == "":
                return 0 


        doc1 = nlp(statement1)
        doc2 = nlp(statement2)
        similarity = doc1.similarity(doc2)

        return similarity*100    
        #return round(similarity * 100, 2)

def extract_error_string(stderr):
    start_token = 'error:'
    start_idx = stderr.find(start_token)
    if start_idx != -1:
        start_idx += len(start_token)
        end_idx = stderr.find('\n', start_idx)
        if end_idx != -1:
            return stderr[start_idx:end_idx].strip()
    return None


def extract_meaningful_error_message_node(error_message):
    error_message = re.sub(r'\x1b\[\d+(;\d+)*m', '', error_message)
    
    match = re.search(r"(TypeError|SyntaxError|ReferenceError|RangeError|EvalError|URIError|Error|error|message): [^\n]+", error_message)
    
    if match:
        return match.group(0)
    return error_message

def extract_meaningful_error_message_deno(error_message):
    # Remove ANSI escape codes
    error_message = re.sub(r'\x1b\[\d+(;\d+)*m', '', error_message)
    error_message = re.sub(r"error: Uncaught \(in promise\) Test262Error\s*", "", error_message)
    
    match = re.search(r"(TypeError|SyntaxError|ReferenceError|RangeError|EvalError|URIError|Error|message|error): [^\n]+", error_message)
    
    if match:
        return match.group(0)
    return error_message   

def preprocess_error(error_message):
    
    error_message = re.sub(r"\S*\.js\S*", '', error_message)  # Remove .js paths
    error_message = re.sub(r'node:\S+', '', error_message)  # Remove node paths
    error_message = re.sub(r'v\d+\.\d+\.\d+', '', error_message)  # Remove Node.js version numbers
    error_message = re.sub(r'\x1b|\bfile://', '', error_message)
    error_message = re.sub(r"\(node:\d+\) Warning:.*\n", '', error_message)
    error_message = re.sub(r"\(Use `node.*trace-warnings.*\n", '', error_message)
    error_message = re.sub(r'\[\d{0,2}m', '', error_message)
    
    return error_message

def check_error_in_stderr(stderr, error_str):
    return error_str.lower() in stderr.lower()

def copy_cluster_files(cluster_dict, source_dir, dest_dir):
    # Iterate over each cluster in the dictionary
    for cluster_name, files in cluster_dict.items():
        # Create the destination subdirectory for the current cluster
        cluster_dest_path = os.path.join(dest_dir, cluster_name)
        os.makedirs(cluster_dest_path, exist_ok=True)
        
        # Copy each file in the cluster to the destination directory
        for file_name in files:
            # Construct the full path of the source file
            source_file_path = os.path.join(source_dir, file_name)
            
            # Only copy if the source file exists
            if os.path.isfile(source_file_path):
                # Copy file to the destination cluster directory
                shutil.copy2(source_file_path, cluster_dest_path)
                print(f"Copied {file_name} to {cluster_dest_path}")
            else:
                print(f"File {file_name} not found in source directory: {source_file_path}")


################################################################# INITIALISATIONS OVER ######################################################################################

def collect_json_files(base_dir):
    result = {}
    
    for root, dirs, files in os.walk(base_dir):
        json_files = [f for f in files if f.endswith('.json')]
        if json_files:

            parent_dir = os.path.basename(root)
            if os.path.basename(root) != os.path.basename(base_dir):
                result[parent_dir] = {}
                for file_name in json_files:
                    file_path = os.path.join(root, file_name)
                    with open(file_path, 'r') as json_file:
                        try:
                            file_content = json.load(json_file)
                            result[parent_dir][file_name] = file_content
                        except json.JSONDecodeError:
                            print(f"Warning: Failed to decode {file_name}, skipping.")
        
    return result

def save_to_json(output_path, data):
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)




collected_data = collect_json_files(base_directory)
save_to_json(output_file, collected_data)
print("Collector Done...")


################################################# END OF COLLECTOR #################################################################


with open(source_separator, 'r') as source_file:
    round_data = json.load(source_file)

timeout_logs = {}
remaining_logs = {}
same_error_logs = {}
panic_logs = {}
sameoutput_logs = {}
dynamic_sameerror_logs = {}

stats = {}

print(round_data.keys())

for round, data in round_data.items():
    round_stats={
        "timeouts" : {
            "total": 0,
            "node" : 0,
            "deno" : 0,
            "bun"  : 0
        },
        "panics" : {
            "node" : 0,
            "deno" : 0,
            "bun" : 0
        },
        "same_output": 0,
        "same_error" : 0, 
        "dynamic_same_error" : 0,

    }
    
    for key, log in data.items():
        #print(round, "    ", key)
        timeout_flag = False
        same_error_flag = False 
        panic_flag = False
        sameoutput_flag = False 
        #address_in_use_flag = False  

        node_log = log.get('node', '').strip()
        deno_log = log.get('deno', '').strip()
        bun_log = log.get('bun', '').strip()

        '''node_preprocessed = preprocess_error(node_log)
        node_preprocessed = extract_meaningful_error_message_node(node_preprocessed)

        deno_preprocessed = preprocess_error(deno_log)
        deno_preprocessed = extract_meaningful_error_message_deno(deno_preprocessed)

        bun_preprocessed = preprocess_error(bun_log)
        bun_preprocessed = extract_meaningful_error_message_node(bun_preprocessed)
        bun_preprocessed = re.sub(r"[^\x00-\x7F]+", "",bun_preprocessed)'''

        
        #if ("panic" in deno_log.lower()) or ("segfault" in node_log.lower()) or ("panic" in bun_log.lower()) or ("fatal error" in node_log.lower()) or ("fatal error" in bun_log.lower()) or ("fatal error" in deno_log.lower()) or ("core dumped" in node_log.lower()) or ("core dumped" in deno_log.lower()) or ("core dumped" in bun_log.lower()):
            #panic_logs[key] = log 
            #panic_flag = True 


        if ("panic" in deno_log.lower()) or ("fatal error" in deno_log.lower()) or ("core dumped" in deno_log.lower()):
            panic_flag = True
            round_stats["panics"]["deno"] = round_stats["panics"]["deno"] + 1
        if  ("panic" in node_log.lower()) or ("segfault" in node_log.lower()) or ("fatal error" in node_log.lower()) or ("core dumped" in node_log.lower()):
            panic_flag = True
            round_stats["panics"]["node"] = round_stats["panics"]["node"] + 1
        if ("panic" in bun_log.lower()) or ("fatal error" in bun_log.lower()) or ("core dumped" in bun_log.lower()):
            panic_flag = True 
            round_stats["panics"]["bun"] = round_stats["panics"]["bun"] + 1
            

        if node_log == "Timeout" or deno_log == "Timeout" or bun_log == "Timeout":
            timeout_flag = True
            round_stats["timeouts"]["total"] = round_stats["timeouts"]["total"] + 1
            
            if node_log == "Timeout": 
                round_stats["timeouts"]["node"] = round_stats["timeouts"]["node"] + 1
            if deno_log == "Timeout": 
                round_stats["timeouts"]["deno"] = round_stats["timeouts"]["deno"] + 1
            if bun_log == "Timeout": 
                round_stats["timeouts"]["bun"] = round_stats["timeouts"]["bun"] + 1
                

        for keyword in keywords:
            if keyword in node_log and keyword in deno_log and keyword in bun_log and timeout_flag != True and sameoutput_flag != True:
                same_error_flag = True 
                round_stats["same_error"] = round_stats["same_error"] + 1
                break

        if node_log == deno_log and deno_log == bun_log and timeout_flag != True and same_error_flag != True:
            sameoutput_flag = True 
            round_stats["same_output"] = round_stats["same_output"] + 1
        '''if node_preprocessed == deno_preprocessed and deno_preprocessed==bun_preprocessed and timeout_flag != True and same_error_flag != True:
            sameoutput_flag = True 
            round_stats["same_output"] = round_stats["same_output"] + 1'''
        
        '''if error_similarity(node_log,deno_log) >= 75 and error_similarity(deno_log,bun_log) >= 75 and error_similarity(node_log,bun_log) >= 75:
            round_stats["dynamic_same_error"] = round_stats["dynamic_same_error"] + 1'''
        '''if error_similarity(node_preprocessed,deno_preprocessed) >= 75 and error_similarity(deno_preprocessed,bun_preprocessed) >= 75 and error_similarity(node_preprocessed,bun_preprocessed) >= 75:
            round_stats["dynamic_same_error"] = round_stats["dynamic_same_error"] + 1'''

        if panic_flag:
            if round not in panic_logs.keys(): 
                panic_logs[round] = {}                        
            panic_logs[round][key] = log 
            continue
        elif timeout_flag:
            if round  not in timeout_logs.keys():
                timeout_logs[round] = {}
            timeout_logs[round][key] = log 
            continue
        elif same_error_flag:
            if round not in same_error_logs.keys():
                same_error_logs[round] = {}
            same_error_logs[round][key] = log 
            continue
        elif sameoutput_flag:
            if round not in sameoutput_logs.keys(): 
                sameoutput_logs[round] = {} 
            sameoutput_logs[round][key] = log 
            continue
        elif error_similarity(node_log,deno_log) >= 99 and error_similarity(deno_log,bun_log) >= 99 and error_similarity(node_log,bun_log) >= 99:
            if round not in dynamic_sameerror_logs.keys(): 
                dynamic_sameerror_logs[round] = {} 
            dynamic_sameerror_logs[round][key] = log 
            continue
        else:
            if round not in remaining_logs.keys(): 
                remaining_logs[round] = {}
            remaining_logs[round][key] = log 
        
        stats[round] = round_stats


# Write logs to op files 

os.makedirs(os.path.join(cwd,"separated"), exist_ok=True)

with open(timeout_file, 'w') as dest_file:
    json.dump(timeout_logs, dest_file, indent=4)

with open(panic_file, 'w') as dest_file:
    json.dump(panic_logs, dest_file, indent=4)

with open(same_error_file, 'w') as dest_file:
    json.dump(same_error_logs, dest_file, indent=4)

with open(sameoutput_file, 'w') as dest_file:
    json.dump(sameoutput_logs, dest_file, indent=4)

with open(dynamic_file, 'w') as dest_file:
    json.dump(dynamic_sameerror_logs, dest_file, indent=4)

with open(diff_error_file, 'w') as dest_file:
    json.dump(remaining_logs, dest_file, indent=4)


print("Separator Done...")


################################################# END OF SEPARATOR #################################################################


with open(source_filter, 'r') as source_file:
    round_data = json.load(source_file)

filter_logs = {}
remaining_logs = {} 

low_level_filter_counts = {}
filter_counts = {}

for round, data in round_data.items():
    print("processing: ", round)
    for key, log in data.items():

            #node_stderr = log.get('node', '').strip()
            node_stderr = (log.get('node') or '')
            #deno_stderr = log.get('deno', '').strip()
            deno_stderr = (log.get('deno') or '')
            #bun_stderr = log.get('bun', '').strip()
            bun_stderr = (log.get('bun') or '')
            error_str = extract_error_string(bun_stderr)

            node_preprocessed = preprocess_error(node_stderr)
            node_preprocessed = extract_meaningful_error_message_node(node_preprocessed)

            deno_preprocessed = preprocess_error(deno_stderr)
            deno_preprocessed = extract_meaningful_error_message_deno(deno_preprocessed)

            bun_preprocessed = preprocess_error(bun_stderr)
            bun_preprocessed = extract_meaningful_error_message_node(bun_preprocessed)
            bun_preprocessed = re.sub(r"[^\x00-\x7F]+", "",bun_preprocessed)

            move = False

            #low level filter 1
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"error") and check_error_in_stderr(bun_stderr,"error:")):
            
                if "low_level_filter_1" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_1"] = 1
                else:
                    low_level_filter_counts["low_level_filter_1"] += 1


                #filter1
                if check_error_in_stderr(node_stderr,"Cannot use"):
                    if check_error_in_stderr(node_stderr,"import"):
                        if check_error_in_stderr(deno_stderr,"import is not allowed"):
                            if check_error_in_stderr(bun_stderr,"Cannot") and check_error_in_stderr(bun_stderr,"import"):
                                move = True

                                if "filter_1" not in filter_counts:
                                    filter_counts["filter_1"] = 1
                                else:
                                    filter_counts["filter_1"] += 1

                    if check_error_in_stderr(node_stderr,"outside a module"):
                        if check_error_in_stderr(deno_stderr,"Invalid destructuring"):
                            if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                                move = True

                                if "filter_1" not in filter_counts:
                                    filter_counts["filter_1"] = 1
                                else:
                                    filter_counts["filter_1"] += 1

                    if check_error_in_stderr(node_stderr,"outside a module"):
                        if check_error_in_stderr(deno_stderr,"Invalid left-hand"):
                            if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                                move = True

                                if "filter_1" not in filter_counts:
                                    filter_counts["filter_1"] = 1
                                else:
                                    filter_counts["filter_1"] += 1

                '''#filter2
                if check_error_in_stderr(node_stderr,"Class constructor"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Class constructor"):
                            move = True'''

                #filter3
                if check_error_in_stderr(node_stderr,"escaped characters"):
                    if check_error_in_stderr(deno_stderr,"escape sequence"):
                        if check_error_in_stderr(bun_stderr,"cannot be escaped"):
                            move = True

                            if "filter_3" not in filter_counts:
                                    filter_counts["filter_3"] = 1
                            else:
                                filter_counts["filter_3"] += 1

                #filter4
                if check_error_in_stderr(node_stderr,"Invalid destructuring"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                            move = True

                            if "filter_4" not in filter_counts:
                                filter_counts["filter_4"] = 1
                            else:
                                filter_counts["filter_4"] += 1

                #filter5
                if check_error_in_stderr(node_stderr,"Invalid left-hand"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                            if "filter_5" not in filter_counts:
                                filter_counts["filter_5"] = 1
                            else:
                                filter_counts["filter_5"] += 1

                #filter6
                if check_error_in_stderr(node_stderr,"Invalid left-hand"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                            move = True

                            if "filter_6" not in filter_counts:
                                filter_counts["filter_6"] = 1
                            else:
                                filter_counts["filter_6"] += 1

                #filter7
                if check_error_in_stderr(node_stderr,"Lexical declaration"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"single-statement context"):
                            move = True

                            if "filter_7" not in filter_counts:
                                filter_counts["filter_7"] = 1
                            else:
                                filter_counts["filter_7"] += 1

                #filter8
                if check_error_in_stderr(node_stderr,"Malformed arrow function"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                            if "filter_8" not in filter_counts:
                                filter_counts["filter_8"] = 1
                            else:
                                filter_counts["filter_8"] += 1

                #filter9
                if check_error_in_stderr(node_stderr,"require a function name"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                            if "filter_9" not in filter_counts:
                                filter_counts["filter_9"] = 1
                            else:
                                filter_counts["filter_9"] += 1

                #filter10
                if check_error_in_stderr(node_stderr,"reserved word"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"cannot be named") or check_error_in_stderr(bun_stderr,"Cannot use"):
                            move = True

                            if "filter_10" not in filter_counts:
                                filter_counts["filter_10"] = 1
                            else:
                                filter_counts["filter_10"] += 1

                #filter11
                if check_error_in_stderr(node_stderr,"strict mode") and check_error_in_stderr(node_stderr,"reserved word"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"reserved word"):
                            move = True

                            if "filter_11" not in filter_counts:
                                filter_counts["filter_11"] = 1
                            else:
                                filter_counts["filter_11"] += 1
                            
        
                #filter12
                if check_error_in_stderr(node_stderr,"super") and check_error_in_stderr(node_stderr,"keyword unexpected"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Unexpected") and check_error_in_stderr(bun_stderr,"super"):
                            move = True

                            if "filter_12" not in filter_counts:
                                filter_counts["filter_12"] = 1
                            else:
                                filter_counts["filter_12"] += 1

                #filter13
                if check_error_in_stderr(node_stderr,"tagged template"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                            if "filter_13" not in filter_counts:
                                filter_counts["filter_13"] = 1
                            else:
                                filter_counts["filter_13"] += 1

                #filter14
                if check_error_in_stderr(node_stderr,"Unary operator"):
                    if check_error_in_stderr(deno_stderr,"unary/await"):
                        if check_error_in_stderr(bun_stderr,"Unexpected"):
                            move = True

                            if "filter_14" not in filter_counts:
                                filter_counts["filter_14"] = 1
                            else:
                                filter_counts["filter_14"] += 1

                #filter15
                if check_error_in_stderr(node_stderr,"Unexpected end of input"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                            if "filter_15" not in filter_counts:
                                filter_counts["filter_15"] = 1
                            else:
                                filter_counts["filter_15"] += 1

                #filter16
                if check_error_in_stderr(node_stderr,"Unexpected string"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                            if "filter_16" not in filter_counts:
                                filter_counts["filter_16"] = 1
                            else:
                                filter_counts["filter_16"] += 1

                #filter17
                if check_error_in_stderr(node_stderr,"Unexpected token"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"must be initialized"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"single-statement context"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"Unexpected switch"):
                            move = True 

                        if move == True:
                            if "filter_17" not in filter_counts:
                                filter_counts["filter_17"] = 1
                            else:
                                filter_counts["filter_17"] += 1

                #filter18
                if check_error_in_stderr(node_stderr,"Yield expression"):
                    if check_error_in_stderr(deno_stderr,"yield") and check_error_in_stderr(deno_stderr,"cannot be used"):
                        if check_error_in_stderr(bun_stderr,"yield") and check_error_in_stderr(bun_stderr,"cannot be used"):
                            move = True

                            if "filter_18" not in filter_counts:
                                filter_counts["filter_18"] = 1
                            else:
                                filter_counts["filter_18"] += 1

            #low level filter 2
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"SyntaxError:") and check_error_in_stderr(bun_stderr,"error:")):    

                if "low_level_filter_2" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_2"] = 1
                else:
                    low_level_filter_counts["low_level_filter_2"] += 1

                #filter19 
                if check_error_in_stderr(node_stderr,"arguments") and check_error_in_stderr(node_stderr,"not allowed"):
                    if check_error_in_stderr(deno_stderr,"arguments") and check_error_in_stderr(deno_stderr,"not allowed"):
                        if check_error_in_stderr(bun_stderr,"Cannot access"):
                            move = True

                            if "filter_19" not in filter_counts:
                                filter_counts["filter_19"] = 1
                            else:
                                filter_counts["filter_19"] += 1
                            

                #filter20
                if check_error_in_stderr(node_stderr,"can only be declared"):
                    if check_error_in_stderr(deno_stderr,"can only be declared"):
                        if check_error_in_stderr(bun_stderr,"single-statement context"):
                            move = True

                            if "filter_20" not in filter_counts:
                                filter_counts["filter_20"] = 1
                            else:
                                filter_counts["filter_20"] += 1

                #filter21
                if check_error_in_stderr(node_stderr,"escaped characters"):
                    if check_error_in_stderr(deno_stderr,"escaped characters"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True		

                            if "filter_21" not in filter_counts:
                                filter_counts["filter_21"] = 1
                            else:
                                filter_counts["filter_21"] += 1	

                #filter22
                if check_error_in_stderr(node_stderr,"for-await-of"):
                    if check_error_in_stderr(deno_stderr,"for-await-of"):
                        if check_error_in_stderr(bun_stderr,"for-of"):
                            move = True

                            if "filter_22" not in filter_counts:
                                filter_counts["filter_22"] = 1
                            else:
                                filter_counts["filter_22"] += 1	

                #filter23
                if check_error_in_stderr(node_stderr,"Generators") and check_error_in_stderr(node_stderr,"declared"):
                    if check_error_in_stderr(deno_stderr,"strict mode"):
                        if check_error_in_stderr(bun_stderr,"single-statement context"):
                            move = True

                            if "filter_23" not in filter_counts:
                                filter_counts["filter_23"] = 1
                            else:
                                filter_counts["filter_23"] += 1
                            

                #filter24
                if check_error_in_stderr(node_stderr,"Getter") and check_error_in_stderr(node_stderr,"formal parameters"):
                    if check_error_in_stderr(deno_stderr,"Getter") and check_error_in_stderr(node_stderr,"formal parameters"):
                        if check_error_in_stderr(bun_stderr,"Getter") and check_error_in_stderr(bun_stderr,"zero arguments"):
                            move = True

                            if "filter_24" not in filter_counts:
                                filter_counts["filter_24"] = 1
                            else:
                                filter_counts["filter_24"] += 1

                #filter25
                if check_error_in_stderr(node_stderr,"Illegal"):
                    if check_error_in_stderr(deno_stderr,"Illegal"):
                        if check_error_in_stderr(bun_stderr,"cannot be used here"):
                            move = True

                            if "filter_25" not in filter_counts:
                                filter_counts["filter_25"] = 1
                            else:
                                filter_counts["filter_25"] += 1
                            

                #filter26
                if check_error_in_stderr(node_stderr,"Illegal break"):
                    if check_error_in_stderr(deno_stderr,"Illegal break"):
                        if check_error_in_stderr(bun_stderr,"Cannot use") and check_error_in_stderr(bun_stderr,"break"):
                            move = True

                            if "filter_26" not in filter_counts:
                                filter_counts["filter_26"] = 1
                            else:
                                filter_counts["filter_26"] += 1
                
                #filter27
                if check_error_in_stderr(node_stderr,"Illegal continue"):
                    if check_error_in_stderr(deno_stderr,"Illegal continue"):
                        if check_error_in_stderr(bun_stderr,"Cannot use") and check_error_in_stderr(bun_stderr,"continue"):
                            move = True

                            if "filter_27" not in filter_counts:
                                filter_counts["filter_27"] = 1
                            else:
                                filter_counts["filter_27"] += 1

                #filter28
                if check_error_in_stderr(node_stderr,"Invalid left-hand"):
                    if check_error_in_stderr(deno_stderr,"Invalid left-hand"):
                        if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                            move = True

                            if "filter_28" not in filter_counts:
                                filter_counts["filter_28"] = 1
                            else:
                                filter_counts["filter_28"] += 1

                #filter29
                if check_error_in_stderr(node_stderr,"Invalid shorthand"):
                    if check_error_in_stderr(deno_stderr,"Invalid shorthand"):
                        if check_error_in_stderr(bun_stderr,"Unexpected"):
                            move = True

                            if "filter_29" not in filter_counts:
                                filter_counts["filter_29"] = 1
                            else:
                                filter_counts["filter_29"] += 1

                #filter30
                if check_error_in_stderr(node_stderr,"is disallowed"):
                    if check_error_in_stderr(deno_stderr,"strict mode"):
                        if check_error_in_stderr(bun_stderr,"Cannot use"):
                            move = True

                            if "filter_30" not in filter_counts:
                                filter_counts["filter_30"] = 1
                            else:
                                filter_counts["filter_30"] += 1

                #filter31
                if check_error_in_stderr(node_stderr,"Missing") and check_error_in_stderr(node_stderr,"catch") and check_error_in_stderr(node_stderr,"finally"):
                    if check_error_in_stderr(deno_stderr,"Missing") and check_error_in_stderr(deno_stderr,"catch") and check_error_in_stderr(deno_stderr,"finally"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                            if "filter_31" not in filter_counts:
                                filter_counts["filter_31"] = 1
                            else:
                                filter_counts["filter_31"] += 1

                #filter32
                if check_error_in_stderr(node_stderr,"not a valid identifier name"):
                    if check_error_in_stderr(deno_stderr,"Unexpected token"):
                        if check_error_in_stderr(bun_stderr,"Unexpected"):
                            move = True

                            if "filter_32" not in filter_counts:
                                filter_counts["filter_32"] = 1
                            else:
                                filter_counts["filter_32"] += 1

                #filter33
                if check_error_in_stderr(node_stderr,"Private field"):
                    if check_error_in_stderr(deno_stderr,"Private field"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                            if "filter_33" not in filter_counts:
                                filter_counts["filter_33"] = 1
                            else:
                                filter_counts["filter_33"] += 1

                        elif check_error_in_stderr(bun_stderr,"Private name"):
                            move = True 

                            if "filter_33" not in filter_counts:
                                filter_counts["filter_33"] = 1
                            else:
                                filter_counts["filter_33"] += 1

                #filter34
                if check_error_in_stderr(node_stderr,"Private fields"):
                    if check_error_in_stderr(deno_stderr,"Private fields"):
                        if check_error_in_stderr(bun_stderr,"Private name"):
                            move = True

                            if "filter_34" not in filter_counts:
                                filter_counts["filter_34"] = 1
                            else:
                                filter_counts["filter_34"] += 1

                #filter35
                if check_error_in_stderr(node_stderr,"regular expression"):
                    if check_error_in_stderr(deno_stderr,"regular expression"):
                        if check_error_in_stderr(bun_stderr,"regular expression"):
                            move = True

                            if "filter_35" not in filter_counts:
                                filter_counts["filter_35"] = 1
                            else:
                                filter_counts["filter_35"] += 1

                #filter36
                if check_error_in_stderr(node_stderr,"reserved word"):
                    if check_error_in_stderr(deno_stderr,"reserved word"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                            if "filter_36" not in filter_counts:
                                filter_counts["filter_36"] = 1
                            else:
                                filter_counts["filter_36"] += 1

                #filter37
                if check_error_in_stderr(node_stderr,"Rest element"):
                    if check_error_in_stderr(deno_stderr,"Rest element"):
                        if check_error_in_stderr(bun_stderr,"rest pattern"):
                            move = True

                            if "filter_37" not in filter_counts:
                                filter_counts["filter_37"] = 1
                            else:
                                filter_counts["filter_37"] += 1

                #filter38
                if check_error_in_stderr(node_stderr,"static property"):
                    if check_error_in_stderr(deno_stderr,"static property"):
                        if check_error_in_stderr(bun_stderr,"Invalid field name") or check_error_in_stderr(bun_stderr,"static method"):
                            move = True

                            if "filter_38" not in filter_counts:
                                filter_counts["filter_38"] = 1
                            else:
                                filter_counts["filter_38"] += 1

                #filter39
                if check_error_in_stderr(node_stderr,"strict mode"):
                    if check_error_in_stderr(deno_stderr,"strict mode"):
                        if check_error_in_stderr(bun_stderr,"single-statement context"):
                            move = True

                            if "filter_39" not in filter_counts:
                                filter_counts["filter_39"] = 1
                            else:
                                filter_counts["filter_39"] += 1

                #filter40
                if check_error_in_stderr(node_stderr,"tagged template"):
                    if check_error_in_stderr(deno_stderr,"tagged template"):
                        if check_error_in_stderr(bun_stderr,"template literals"):
                            move = True

                            if "filter_40" not in filter_counts:
                                filter_counts["filter_40"] = 1
                            else:
                                filter_counts["filter_40"] += 1

                #filter41
                if check_error_in_stderr(node_stderr,"top level bodies"):
                    if check_error_in_stderr(deno_stderr,"reserved word"):
                        if check_error_in_stderr(bun_stderr,"can only be used"):
                            move = True

                            if "filter_41" not in filter_counts:
                                filter_counts["filter_41"] = 1
                            else:
                                filter_counts["filter_41"] += 1

                #filter42
                if check_error_in_stderr(node_stderr,"Undefined label"):
                    if check_error_in_stderr(deno_stderr,"Undefined label"):
                        if check_error_in_stderr(bun_stderr,"containing label"):
                            move = True

                            if "filter_42" not in filter_counts:
                                filter_counts["filter_42"] = 1
                            else:
                                filter_counts["filter_42"] += 1

                #filter43
                if check_error_in_stderr(node_stderr,"Unexpected eval"):
                    if check_error_in_stderr(deno_stderr,"Unexpected eval"):
                        if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"cannot be used"):
                            move = True

                            if "filter_43" not in filter_counts:
                                filter_counts["filter_43"] = 1
                            else:
                                filter_counts["filter_43"] += 1

                #filter44
                if check_error_in_stderr(node_stderr,"Unexpected identifier"):
                    if check_error_in_stderr(deno_stderr,"reserved word"):
                        if check_error_in_stderr(bun_stderr,"cannot be escaped") or check_error_in_stderr(bun_stderr,"Cannot use"):
                            move = True

                            if "filter_44" not in filter_counts:
                                filter_counts["filter_44"] = 1
                            else:
                                filter_counts["filter_44"] += 1

                #filter45
                if check_error_in_stderr(node_stderr,"Unexpected number"):
                    if check_error_in_stderr(deno_stderr,"reserved word"):
                        if check_error_in_stderr(bun_stderr,"can only be used"):
                            move = True

                            if "filter_45" not in filter_counts:
                                filter_counts["filter_45"] = 1
                            else:
                                filter_counts["filter_45"] += 1

                #filter46
                if check_error_in_stderr(node_stderr,"Unexpected string"):
                    if check_error_in_stderr(deno_stderr,"Unexpected string"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                            if "filter_46" not in filter_counts:
                                filter_counts["filter_46"] = 1
                            else:
                                filter_counts["filter_46"] += 1

                #filter47
                if check_error_in_stderr(node_stderr,"Unexpected token") or check_error_in_stderr(node_stderr,"Unexpected identifier"):
                    if check_error_in_stderr(deno_stderr,"Unexpected token"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                            if "filter_47" not in filter_counts:
                                filter_counts["filter_47"] = 1
                            else:
                                filter_counts["filter_47"] += 1

                        elif check_error_in_stderr(bun_stderr,"Unexpected"):
                            move = True

                            if "filter_47" not in filter_counts:
                                filter_counts["filter_47"] = 1
                            else:
                                filter_counts["filter_47"] += 1

            #low level filter 3 
            if (check_error_in_stderr(node_stderr,"Error ") and check_error_in_stderr(deno_stderr,"TypeError:") and check_error_in_stderr(bun_stderr,"error:")):
                
                if "low_level_filter_3" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_3"] = 1
                else:
                    low_level_filter_counts["low_level_filter_3"] += 1

                #filter48   
                if check_error_in_stderr(node_stderr,"Cannot find module"):
                    if check_error_in_stderr(deno_stderr,"Module not found"):
                        if check_error_in_stderr(bun_stderr,"Cannot find module"):
                            move = True

                            if "filter_48" not in filter_counts:
                                filter_counts["filter_48"] = 1
                            else:
                                filter_counts["filter_48"] += 1

                #filter49
                if check_error_in_stderr(node_stderr,"Cannot find package"):
                    if check_error_in_stderr(deno_stderr,"TypeError"):
                        if check_error_in_stderr(bun_stderr,"Cannot find package"):
                            move = True

                            if "filter_49" not in filter_counts:
                                filter_counts["filter_49"] = 1
                            else:
                                filter_counts["filter_49"] += 1

            #low level filter 4 
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"error") and check_error_in_stderr(bun_stderr,"SyntaxError:")):
            
                if "low_level_filter_4" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_4"] = 1
                else:
                    low_level_filter_counts["low_level_filter_4"] += 1
                
                #filter50
                if check_error_in_stderr(node_stderr,"for-in"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"for-in"):
                            move = True

                            if "filter_50" not in filter_counts:
                                filter_counts["filter_50"] = 1
                            else:
                                filter_counts["filter_50"] += 1
                
                #filter51
                if check_error_in_stderr(node_stderr,"reserved word"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Cannot declare"):
                            move = True

                            if "filter_51" not in filter_counts:
                                filter_counts["filter_51"] = 1
                            else:
                                filter_counts["filter_51"] += 1

            #low level filter 5
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"error") and check_error_in_stderr(bun_stderr,"error:") and check_error_in_stderr(bun_stderr,"Syntax Error")):

                if "low_level_filter_5" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_5"] = 1
                else:
                    low_level_filter_counts["low_level_filter_5"] += 1

                #filter52
                if check_error_in_stderr(node_stderr,"regular expression"):
                    if check_error_in_stderr(deno_stderr,"regexp literal"):
                        if check_error_in_stderr(bun_stderr,"Syntax Error"):
                            move = True

                            if "filter_52" not in filter_counts:
                                filter_counts["filter_52"] = 1
                            else:
                                filter_counts["filter_52"] += 1

                #filter53
                if check_error_in_stderr(node_stderr,"unexpected token"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Syntax Error"):
                            move = True

                            if "filter_53" not in filter_counts:
                                filter_counts["filter_53"] = 1
                            else:
                                filter_counts["filter_53"] += 1

                #filter54
                if check_error_in_stderr(node_stderr,"Cannot use") and check_error_in_stderr(node_stderr,"outside a module"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed") and check_error_in_stderr(deno_stderr,"Invalid assignment target"):
                        if check_error_in_stderr(bun_stderr,"Invalid assignment target"):
                            move=True

                            if "filter_54" not in filter_counts:
                                filter_counts["filter_54"] = 1
                            else:
                                filter_counts["filter_54"] += 1

            #low level filter 6 
            if error_str:
                if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"Test262Error"):
                    if check_error_in_stderr(node_stderr,error_str) and check_error_in_stderr(deno_stderr,error_str):
                        print("detected test262 error")
                        move = True

                        if "low_level_filter_6" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_6"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_6"] += 1

                if check_error_in_stderr(node_stderr,"Test262Error"):
                    if check_error_in_stderr(node_stderr,error_str):
                        if check_error_in_stderr(deno_stderr,"has already been declared"):
                            move = True
                        elif check_error_in_stderr(deno_stderr,"may not include a with statement"):
                            move = True
                        elif check_error_in_stderr(deno_stderr,"Cannot ") and check_error_in_stderr(deno_stderr,"properties of undefined"):
                            move = True
                        elif check_error_in_stderr(deno_stderr,"Unexpected eval or arguments") and check_error_in_stderr(deno_stderr,"in strict mode"): 
                            move = True
                        elif check_error_in_stderr(deno_stderr,"TypeError:") and check_error_in_stderr(deno_stderr,"Object.defineProperty called on non-object"):
                            move = True

                        if move==True:
                            if "low_level_filter_6" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_6"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_6"] += 1

            #filter55
            if check_error_in_stderr(node_stderr,"EADDRINUSE"):
                if check_error_in_stderr(bun_stderr,"EADDRINUSE"):
                    if check_error_in_stderr(deno_stderr,"AddrInUse") or check_error_in_stderr(deno_stderr,"has already been declared") or check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                        move = True

                        if "filter_55" not in filter_counts:
                            filter_counts["filter_55"] = 1
                        else:
                            filter_counts["filter_55"] += 1


            #low level filter 7
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"SyntaxError:") and check_error_in_stderr(bun_stderr,"Syntax Error")):
                move = True

                if "low_level_filter_7" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_7"] = 1
                else:
                    low_level_filter_counts["low_level_filter_7"] += 1

            #low level filter 8
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"SyntaxError") and check_error_in_stderr(deno_stderr,"error") and check_error_in_stderr(bun_stderr,"error:")):
                
                if "low_level_filter_8" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_8"] = 1
                else:
                    low_level_filter_counts["low_level_filter_8"] += 1
                
                #filter56
                if check_error_in_stderr(node_stderr,"Invalid") and check_error_in_stderr(node_stderr,"unexpected") and check_error_in_stderr(node_stderr,"token"):
                    if check_error_in_stderr(deno_stderr,"Invalid") and check_error_in_stderr(deno_stderr,"unexpected") and check_error_in_stderr(deno_stderr,"token"):
                        if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"identifier"):
                            move = True

                            if "filter_56" not in filter_counts:
                                filter_counts["filter_56"] = 1
                            else:
                                filter_counts["filter_56"] += 1

             

            #low level filter 9
            if check_error_in_stderr(node_stderr,"Server running at"):
                if check_error_in_stderr(deno_stderr,"Server running at"):
                    if check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True

                        if "low_level_filter_9" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_9"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_9"] += 1

            #low level filter 10
            if node_stderr == "" or node_stderr is None:
                if deno_stderr == bun_stderr:
                    move = True 
                    if "low_level_filter_10" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_10"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_10"] += 1
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True 
                    if "low_level_filter_10" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_10"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_10"] += 1
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                    if "low_level_filter_10" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_10"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_10"] += 1
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                    if "low_level_filter_10" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_10"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_10"] += 1
                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                    if "low_level_filter_10" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_10"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_10"] += 1
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True
                    if "low_level_filter_10" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_10"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_10"] += 1
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                    if "low_level_filter_10" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_10"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_10"] += 1
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                    if "low_level_filter_10" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_10"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_10"] += 1
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True
                 
                    if "low_level_filter_10" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_10"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_10"] += 1

                elif bun_stderr == "" or bun_stderr == None:
                    if check_error_in_stderr(deno_stderr,"has already been declared"):
                        move = True

                        if "low_level_filter_10" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_10"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_10"] += 1

                elif check_error_in_stderr(deno_stderr,"ReferenceError:") and check_error_in_stderr(deno_stderr,"is not defined"):
                    if check_error_in_stderr(deno_stderr,"ReferenceError:") and check_error_in_stderr(bun_stderr,"Can't find variable"):
                        move = True

                        if "low_level_filter_10" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_10"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_10"] += 1

            #low level filter 11 
            if check_error_in_stderr(node_stderr,"has already been declared") or check_error_in_stderr(node_stderr,"is not callable") or check_error_in_stderr(node_stderr,"is not defined"):
                if check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"has already been declared") or check_error_in_stderr(bun_stderr,"that shadows a"):
                        move = True

                    elif check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"Expected SameValue") and check_error_in_stderr(bun_stderr,"to be true"):
                        move = True 

                    elif check_error_in_stderr(bun_stderr,"Full Path: ") or check_error_in_stderr(bun_stderr,"Response: ") or check_error_in_stderr(bun_stderr,"Server running at") or check_error_in_stderr(bun_stderr,"subprocess forked") or check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True  
                    
                    elif check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                        move = True 

                    if move and "low_level_filter_11" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_11"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_11"] += 1

                elif deno_stderr == "":
                    if check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"function(){return 1} > function(){return 1}"):
                        move = True 

                elif check_error_in_stderr(deno_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"should match"):
                    if check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"ReferenceError: Can't find variable"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"IP Address 1: "):
                        move = True

                    if move and "low_level_filter_11" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_11"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_11"] += 1



            #low level filter 12
            if node_stderr == bun_stderr or node_preprocessed==bun_preprocessed:
                if check_error_in_stderr(deno_stderr,"has already been declared"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"Expected SameValue") and check_error_in_stderr(deno_stderr,"to be true"):
                    move = True 

                if move and "low_level_filter_12" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_12"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_12"] += 1

            #low level filter 13
            if node_stderr == "" or node_stderr == None:
                if deno_stderr == "" or deno_stderr == None:
                    if check_error_in_stderr(bun_stderr,"should match"):
                        move = True

                        if "low_level_filter_13" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_13"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_13"] += 1

            #low level filter 14
            if check_error_in_stderr(deno_stderr,"The import attribute type of") and check_error_in_stderr(deno_stderr,"is unsupported"):
                if check_error_in_stderr(bun_stderr,"cannot use export statement with") and check_error_in_stderr(bun_stderr,"attribute"):
                    move=True

                    if "low_level_filter_14" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_14"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_14"] += 1

            if check_error_in_stderr(deno_stderr,"Uncaught SyntaxError:") and check_error_in_stderr(deno_stderr,"Duplicate export of"):
                if check_error_in_stderr(bun_stderr,"Multiple exports with the same name"):
                    move=True

                    if "low_level_filter_14" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_14"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_14"] += 1
            
            #low level filter 15
            if node_stderr == bun_stderr and check_error_in_stderr(deno_stderr, "Permission denied (os error 13)"):
                move = True 

                if "low_level_filter_15" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_15"] = 1
                else:
                    low_level_filter_counts["low_level_filter_15"] += 1

            #low level filter 16
            if check_error_in_stderr(node_stderr, "is not a function"):
                if deno_stderr == bun_stderr or (deno_stderr == "" and bun_stderr == ""):
                    move = True
                #elif check_error_in_stderr(deno_stderr,"") and check_error_in_stderr(bun_stderr,""):


                    if "low_level_filter_16" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_16"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_16"] += 1

            #low level filter 16
            if check_error_in_stderr(node_stderr, "ReferenceError: ") and check_error_in_stderr(node_stderr,"is not defined"):
                if deno_stderr == "" and bun_stderr == "":
                    move = True

                    if "low_level_filter_16" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_16"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_16"] += 1


            #low level filter 17 
            if check_error_in_stderr(node_stderr,"subprocess killed"):
                if check_error_in_stderr(deno_stderr,"process killed"):
                    if check_error_in_stderr(bun_stderr,"subprocess killed"):
                        move = True

                        if "low_level_filter_17" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_17"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_17"] += 1

            #low level filter 18 
            if check_error_in_stderr(node_stderr,"TypeError:"):
                if check_error_in_stderr(node_stderr,"Cannot set property") and check_error_in_stderr(node_stderr,"which has only a getter"):

                    if "low_level_filter_18" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_18"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_18"] += 1

                    
                    #filter57
                    if check_error_in_stderr(deno_stderr,"subprocess killed"):
                        if check_error_in_stderr(bun_stderr,"subprocess killed"):
                            move = True 

                            if "filter_57" not in filter_counts:
                                filter_counts["filter_57"] = 1
                            else:
                                filter_counts["filter_57"] += 1

                    #filter58
                    if check_error_in_stderr(deno_stderr,"Current HOME Directory: "):
                        if check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                            move = True

                            if "filter_58" not in filter_counts:
                                filter_counts["filter_58"] = 1
                            else:
                                filter_counts["filter_58"] += 1 

                    #filter59
                    if check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"<HTML>"):
                        if check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                            move = True 

                            if "filter_59" not in filter_counts:
                                filter_counts["filter_59"] = 1
                            else:
                                filter_counts["filter_59"] += 1

                    #filter60
                    if (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")):
                        if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                            move = True

                            if "filter_60" not in filter_counts:
                                filter_counts["filter_60"] = 1
                            else:
                                filter_counts["filter_60"] += 1

                    #filter61
                    if deno_stderr == bun_stderr:
                            move = True

                            if "filter_61" not in filter_counts:
                                filter_counts["filter_61"] = 1
                            else:
                                filter_counts["filter_61"] += 1

                    #filter62
                    if check_error_in_stderr(deno_stderr,"Server running at "):
                        if check_error_in_stderr(bun_stderr,"Server running at "):
                            move = True

                            if "filter_62" not in filter_counts:
                                filter_counts["filter_62"] = 1
                            else:
                                filter_counts["filter_62"] += 1

                    #filter63
                    if check_error_in_stderr(deno_stderr,"Uncaught (in promise)"):
                        if check_error_in_stderr(bun_stderr,"Expected a") and check_error_in_stderr(bun_stderr,"but got a"):
                            move = True 

                            if "filter_63" not in filter_counts:
                                filter_counts["filter_63"] = 1
                            else:
                                filter_counts["filter_63"] += 1

                        elif check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                            move = True 

                            if "filter_63" not in filter_counts:
                                filter_counts["filter_63"] = 1
                            else:
                                filter_counts["filter_63"] += 1

                        elif check_error_in_stderr(node_stderr,"Client code can adversely affect behavior"): 
                            if check_error_in_stderr(bun_stderr,"Full Path: ") or check_error_in_stderr(bun_stderr,"Server running at ") or check_error_in_stderr(bun_stderr,"subprocess forked") or check_error_in_stderr(bun_stderr,"Response: ") or check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin/bash") or check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                                move = True 

                                if "filter_63" not in filter_counts:
                                    filter_counts["filter_63"] = 1
                                else:
                                    filter_counts["filter_63"] += 1

                    #filter64
                    if check_error_in_stderr(deno_stderr,"has already been declared"):
                        if check_error_in_stderr(bun_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz"):
                            move = True 

                            if "filter_64" not in filter_counts:
                                filter_counts["filter_64"] = 1
                            else:
                                filter_counts["filter_64"] += 1

                        elif check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"Expected SameValue"):
                            move = True 

                            if "filter_64" not in filter_counts:
                                filter_counts["filter_64"] = 1
                            else:
                                filter_counts["filter_64"] += 1

                        elif check_error_in_stderr(bun_stderr,"Response: ") or check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"Server running at") or check_error_in_stderr(bun_stderr,"subprocess forked"):
                            move = True 

                            if "filter_64" not in filter_counts:
                                filter_counts["filter_64"] = 1
                            else:
                                filter_counts["filter_64"] += 1

                        elif check_error_in_stderr(bun_stderr,"error: No such file or directory"):
                            move = True 
                            
                            if "filter_64" not in filter_counts:
                                filter_counts["filter_64"] = 1
                            else:
                                filter_counts["filter_64"] += 1



            #low level filter 18
            if check_error_in_stderr(node_stderr,"TypeError:"):
                if check_error_in_stderr(node_stderr,"Cannot destructure property") and check_error_in_stderr(node_stderr,"as it is undefined"):
                    if check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"<HTML>"):
                        if check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                            move = True 

                    elif check_error_in_stderr(deno_stderr,"No such file or directory (os error ") and check_error_in_stderr(bun_stderr,"error: No such file or directory"):
                        move = True 

                    if move and "low_level_filter_18" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_18"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_18"] += 1

            #low level filter 19 
            if check_error_in_stderr(node_stderr,"TypeError:") and check_error_in_stderr(bun_stderr,"TypeError:"):
                if check_error_in_stderr(node_stderr,"undefined is not iterable") or check_error_in_stderr(node_stderr,"Cannot read properties of undefined"):
                    if check_error_in_stderr(bun_stderr,"undefined is not an object"):
                        if len(deno_stderr) > 5000:
                            move = True 

                            if "low_level_filter_19" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_19"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_19"] += 1

            #low level filter 20 
            if node_stderr == "" or check_error_in_stderr(node_stderr,"Response: ") or check_error_in_stderr(node_stderr,"Full Path: ") or check_error_in_stderr(node_stderr,"IP Address 1 ") or check_error_in_stderr(node_stderr,"subprocess forked") or check_error_in_stderr(node_stderr,"Current HOME Directory: ") or check_error_in_stderr(node_stderr,"Full Path: ") or check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(node_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz\n"):
                if check_error_in_stderr(deno_stderr,"has already been declared"):
                    if (check_error_in_stderr(bun_stderr,"error:") and check_error_in_stderr(bun_stderr,"No such file or directory")) or check_error_in_stderr(bun_stderr,"SyntaxError"): 
                        move = True 

                        if "low_level_filter_20" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_20"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_20"] += 1
            
            #low level filter 21
            if check_error_in_stderr(node_stderr, "node:internal/async_hooks:541"):
                if deno_stderr == bun_stderr or (deno_stderr == "" and bun_stderr == ""):
                    move = True

                    if "low_level_filter_21" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_21"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_21"] += 1

            #low level filter 22
            if check_error_in_stderr(node_stderr, "node:internal/streams/writable:778"):
                if deno_stderr == "" or check_error_in_stderr(deno_stderr, "Error:"):
                    move = True

                    if "low_level_filter_22" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_22"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_22"] += 1
            
            #low level filter 23 
            if check_error_in_stderr(node_stderr, "node:internal/deps/undici/undici:576"):
                #if (deno_stderr == "" and bun_stderr == "") or deno_stderr == bun_stderr:
                    move = True

                    if "low_level_filter_23" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_23"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_23"] += 1

            #low level filter 24 
            if check_error_in_stderr(node_stderr, "node:path:124"):
                if (deno_stderr == "" and bun_stderr == "") or deno_stderr == bun_stderr:
                    move = True

                    if "low_level_filter_24" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_24"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_24"] += 1

            #low level filter 25
            if check_error_in_stderr(deno_stderr, "should match"):
                if (node_stderr == "" and bun_stderr == "") or node_stderr == bun_stderr:
                    move = True

                    if "low_level_filter_25" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_25"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_25"] += 1

            #low level filter 26 
            # has already been declared
            if check_error_in_stderr(deno_stderr, "has already been declared"):
                if node_stderr == "" and check_error_in_stderr(bun_stderr,"SyntaxError: Cannot declare a var variable that shadows"):
                    move = True

                    if "low_level_filter_26" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_26"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_26"] += 1

            #low level filter 27 
            if check_error_in_stderr(deno_stderr, "Client code can adversely affect behavior: setter for 1"):
                if check_error_in_stderr(bun_stderr, "Client code can adversely affect behavior: setter for 1"):
                    if check_error_in_stderr(node_stderr, "Client code can adversely affect behavior: setter for 1"):
                        move = True

                        if "low_level_filter_27" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_27"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_27"] += 1

            #low level filter 28
            if check_error_in_stderr(node_stderr,"spawn is not defined"):
                if check_error_in_stderr(deno_stderr,"subprocess forked"):
                    if check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True 

                        if "low_level_filter_28" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_28"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_28"] += 1

            #low_level_filter_29
            if check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(node_stderr,"Server closed after 1.5 seconds"):
                if check_error_in_stderr(deno_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server closed after 1.5 seconds"):
                        move = True 

                        if "low_level_filter_29" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_29"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_29"] += 1

            #low_level_filter_30
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"TypeError: "):
                
                if "low_level_filter_30" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_30"] = 1
                else:
                    low_level_filter_counts["low_level_filter_30"] += 1

                #filter65
                if check_error_in_stderr(node_stderr,"is not a function") and check_error_in_stderr(deno_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"is not a function"):
                    move = True 

                    if "filter_65" not in filter_counts:
                        filter_counts["filter_65"] = 1
                    else:
                        filter_counts["filter_65"] += 1

                #filter66
                if check_error_in_stderr(node_stderr,"Cannot read properties of undefined") and check_error_in_stderr(deno_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"undefined is not an object"):
                    move = True 

                    if "filter_66" not in filter_counts:
                        filter_counts["filter_66"] = 1
                    else:
                        filter_counts["filter_66"] += 1


            #low_level_filter_31
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"SyntaxError: "):
                
                if "low_level_filter_31" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_31"] = 1
                else:
                    low_level_filter_counts["low_level_filter_31"] += 1

                #filter67
                if check_error_in_stderr(node_stderr,"is not a function") and check_error_in_stderr(deno_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"that shadows a"):
                    move = True 

                    if "filter_67" not in filter_counts:
                        filter_counts["filter_67"] = 1
                    else:
                        filter_counts["filter_67"] += 1

            #low_level_filter_32
            if check_error_in_stderr(deno_stderr,"Uncaught (in promise) NotFound: No such file or directory") and check_error_in_stderr(deno_stderr,"DenoOutput.txt"):
                if check_error_in_stderr(node_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True

                    if "low_level_filter_32" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_32"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_32"] += 1

            if check_error_in_stderr(deno_stderr,"Uncaught (in promise) NotFound: No such file or directory") and check_error_in_stderr(deno_stderr,"DenoOutput.txt"):
                if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"error: No such file or directory"):
                    move = True

                    if "low_level_filter_32" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_32"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_32"] += 1

            if check_error_in_stderr(deno_stderr,"Uncaught (in promise) NotFound: No such file or directory") and check_error_in_stderr(deno_stderr,"DenoOutput.txt"):
                if check_error_in_stderr(node_stderr,"subprocess forked\nsubprocess killed\n") and check_error_in_stderr(bun_stderr,"error: No such file or directory"):
                    move = True

                    if "low_level_filter_32" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_32"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_32"] += 1

            #low level filter 33
            if check_error_in_stderr(node_stderr,"Current HOME Directory: ") and check_error_in_stderr(deno_stderr,"Current HOME Directory: "):
                if check_error_in_stderr(bun_stderr,"error: No such file or directory"):
                    move=True 

                    if "low_level_filter_33" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_33"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_33"] += 1

            #low level filter 34
            if check_error_in_stderr(deno_stderr,"Uncaught (in promise)"):
                if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"message: "):
                    if check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"message: "):
                        msg1 = re.search(r'message: "(.*?)"',node_stderr)
                        msg2 = re.search(r'message: "(.*?)"',bun_stderr)
                        if msg1 and msg1.group(1) in bun_stderr: 
                            move=True
                        
                        if msg2 and msg2.group(1) in node_stderr: 
                            move=True

                        if move and "low_level_filter_34" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_34"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_34"] += 1

                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz") or check_error_in_stderr(bun_stderr,"Full Path: ") or check_error_in_stderr(bun_stderr,"Response: ") or check_error_in_stderr(bun_stderr,"Server running at ") or check_error_in_stderr(bun_stderr,"Full Path: ") or check_error_in_stderr(bun_stderr,"IP Address 1: ") or check_error_in_stderr(bun_stderr,"subprocess forked"):
                        msg1 = re.search(r'message: "(.*?)"',node_stderr)
                        msg2 = re.search(r"message:\s*['\"](.*?)['\"]", node_stderr)
                        if msg1 and msg1.group(1) in deno_stderr:
                            move = True 

                            if "low_level_filter_34" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_34"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_34"] += 1

                        elif msg2 and msg2.group(1) in deno_stderr:
                            move = True 

                            if "low_level_filter_34" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_34"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_34"] += 1

                 

            #low level filter 35
            if check_error_in_stderr(node_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"message: "):
                if check_error_in_stderr(node_stderr,"has already been declared"):
                    msg = re.search(r'message: "(.*?)"',deno_stderr)
                    if msg and msg.group(1) in node_stderr: 
                        move=True

                        if "low_level_filter_35" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_35"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_35"] += 1

            #low level filter 36
            if check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"SyntaxError: "):
                    
                if "low_level_filter_36" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_36"] = 1
                else:
                    low_level_filter_counts["low_level_filter_36"] += 1                
                
                #filter68
                if "/home/abdullah/node-deno-bun/fuzz/testFuzz\n\n" == node_stderr or check_error_in_stderr(node_stderr,"Current HOME Directory: ") or (check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"Expected") and check_error_in_stderr(node_stderr,"but got")):
                    if check_error_in_stderr(deno_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"Cannot declare") and check_error_in_stderr(bun_stderr,"that shadows a"):
                        move=True

                        if "filter_68" not in filter_counts:
                            filter_counts["filter_68"] = 1
                        else:
                            filter_counts["filter_68"] += 1

                    elif deno_stderr == bun_stderr:
                        move = True 

                        if "filter_68" not in filter_counts:
                            filter_counts["filter_68"] = 1
                        else:
                            filter_counts["filter_68"] += 1

                    elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                        move = True 

                        if "filter_68" not in filter_counts:
                            filter_counts["filter_68"] = 1
                        else:
                            filter_counts["filter_68"] += 1

                    elif check_error_in_stderr(deno_stderr,"Server running at ") and check_error_in_stderr(bun_stderr,"Server running at "):
                        move = True 

                        if "filter_68" not in filter_counts:
                            filter_counts["filter_68"] = 1
                        else:
                            filter_counts["filter_68"] += 1

                    

                #filter69
                if check_error_in_stderr(node_stderr,"Response: "):
                    if check_error_in_stderr(deno_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"Cannot declare") and check_error_in_stderr(bun_stderr,"that shadows a"):
                        move = True 

                        if "filter_69" not in filter_counts:
                            filter_counts["filter_69"] = 1
                        else:
                            filter_counts["filter_69"] += 1

                #filter70
                if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    if check_error_in_stderr(deno_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"Cannot declare") and check_error_in_stderr(bun_stderr,"that shadows a"):
                        move = True 

                        if "filter_70" not in filter_counts:
                            filter_counts["filter_70"] = 1
                        else:
                            filter_counts["filter_70"] += 1


            #low level filter 37
            if check_error_in_stderr(deno_stderr,"Uncaught (in promise) NotFound: No such file or directory"):
                if check_error_in_stderr("error: No such file or directory",bun_stderr):
                    if "/home/abdullah/node-deno-bun/fuzz/testFuzz\n\n" == node_stderr:
                        move=True

                        if "low_level_filter_37" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_37"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_37"] += 1

            #low level filter 38
            if check_error_in_stderr(node_stderr,"RangeError: ") and check_error_in_stderr(deno_stderr,"RangeError: "):
                if check_error_in_stderr("Maximum call stack size exceeded",node_stderr) and check_error_in_stderr("Maximum call stack size exceeded",deno_stderr):
                    if check_error_in_stderr(bun_stderr,"Server running at "):
                        move=True

                        if "low_level_filter_38" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_38"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_38"] += 1

            #low level filter 39
            if check_error_in_stderr(node_stderr,"SyntaxError: ") and check_error_in_stderr(node_stderr,"has already been declared"):
                
                if "low_level_filter_39" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_39"] = 1
                else:
                    low_level_filter_counts["low_level_filter_39"] += 1

                #filter71
                if check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"<HTML>"):
                    if check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                        move = True 
                        
                        if "filter_71" not in filter_counts:
                            filter_counts["filter_71"] = 1
                        else:
                            filter_counts["filter_71"] += 1

                #filter72
                if (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 
                        
                        if "filter_72" not in filter_counts:
                            filter_counts["filter_72"] = 1
                        else:
                            filter_counts["filter_72"] += 1

                #filter73
                if check_error_in_stderr(deno_stderr,"module's source code could not be parsed:") and check_error_in_stderr(deno_stderr,"Unexpected token"):
                    if check_error_in_stderr(bun_stderr,"error: ") and check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"but found "):
                        move = True 
                        
                        if "filter_73" not in filter_counts:
                            filter_counts["filter_73"] = 1
                        else:
                            filter_counts["filter_73"] += 1

                #filter74
                if check_error_in_stderr(deno_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"TypeError: "):
                    if check_error_in_stderr(deno_stderr,"Cannot assign to read only property"):
                        if check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                            move = True 

                            if "filter_74" not in filter_counts:
                                filter_counts["filter_74"] = 1
                            else:
                                filter_counts["filter_74"] += 1



            #low level filter 40
            if check_error_in_stderr(node_stderr,"undefined") and check_error_in_stderr(node_stderr,"node --trace-uncaught"):
                if check_error_in_stderr(deno_stderr,"Uncaught (in promise) undefined"):
                    if check_error_in_stderr(bun_stderr,"error: undefined"):
                        move = True 

                        if "low_level_filter_40" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_40"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_40"] += 1

            #low level filter 41
            if check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(node_stderr,"<HTML>"):
                if check_error_in_stderr(deno_stderr,"No such file or directory"):
                    if check_error_in_stderr(bun_stderr,"error: ") and check_error_in_stderr(bun_stderr,"No such file or directory"):
                        move = True 

                        if "low_level_filter_41" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_41"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_41"] += 1

            #low level filter 42
            if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"SyntaxError: "):
                if check_error_in_stderr(node_stderr,"Expected a ") and check_error_in_stderr(node_stderr,"but no exception was thrown at all"):
                    if check_error_in_stderr(deno_stderr,"has already been declared"):
                        if check_error_in_stderr(bun_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"Cannot declare a") and check_error_in_stderr(bun_stderr,"that shadows a"):
                            move = True 
                        elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                            move = True 
                        elif check_error_in_stderr(bun_stderr,"Response: "):
                            move = True 
                        elif check_error_in_stderr(bun_stderr,"Server running at"):
                            move = True 
                        elif check_error_in_stderr(bun_stderr,"has already been declared"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"Full Path: "):
                            move = True

                        if move and "low_level_filter_42" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_42"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_42"] += 1


            #low level filter 43
            if check_error_in_stderr(node_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"The module's source code could not be parsed: ") and check_error_in_stderr(bun_stderr,"error: "):
                if check_error_in_stderr(node_stderr,"Unexpected identifier ") and check_error_in_stderr(node_stderr,"Unexpected token"):
                    if check_error_in_stderr(bun_stderr,"expected") and check_error_in_stderr(bun_stderr,"but found"):
                        move = True 

                        if "low_level_filter_43" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_43"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_43"] += 1

            #low level filter 44
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"TypeError: "):
                if check_error_in_stderr(node_stderr,"is not a constructor"):
                    if check_error_in_stderr(deno_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"is not a constructor"):
                        move = True 

                        if "low_level_filter_44" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_44"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_44"] += 1

            #low level filter 45
            if check_error_in_stderr(deno_stderr,"No such file or directory"):
                if node_stderr == "" and bun_stderr == "":
                    move = True 

                    if "low_level_filter_45" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_45"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_45"] += 1

            if check_error_in_stderr(deno_stderr,"No such file or directory"):
                if node_stderr == "" and check_error_in_stderr(bun_stderr,"error: No such file or directory"):
                    move = True 

                    if "low_level_filter_45" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_45"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_45"] += 1

            if check_error_in_stderr(deno_stderr,"No such file or directory"):
                if check_error_in_stderr(node_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"error: No such file or directory"):
                    move = True 

                    if "low_level_filter_45" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_45"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_45"] += 1

                elif check_error_in_stderr(bun_stderr,"error: No such file or directory"):
                    if check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"IP Address 1"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"is not defined") or check_error_in_stderr(node_stderr,"has already been declared"):
                        move = True 

            #low level filter 46
            if check_error_in_stderr(node_stderr,"ReferenceError: ") and check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"ReferenceError: "):
                if check_error_in_stderr(node_stderr,"is not defined") and check_error_in_stderr(bun_stderr,"Can't find variable"):
                    if check_error_in_stderr(deno_stderr,"has already been declared"):
                        move = True 

                        if "low_level_filter_46" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_46"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_46"] += 1

            #low level filter 47
            if check_error_in_stderr(deno_stderr,"ReferenceError: ") and check_error_in_stderr(bun_stderr,"ReferenceError: "):
                if check_error_in_stderr(deno_stderr,"is not defined") and check_error_in_stderr(bun_stderr,"Can't find variable"):
                    if check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                        move = True 

                        if "low_level_filter_47" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_47"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_47"] += 1


            #low level filter 48
            if check_error_in_stderr(node_stderr,"RangeError: "):
                if check_error_in_stderr(node_stderr,"Maximum call stack size exceeded"):
                    if check_error_in_stderr(deno_stderr,"Server running at ") and check_error_in_stderr(bun_stderr,"Server running at "):
                        move = True  

                    elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                        move = True

                    elif check_error_in_stderr(deno_stderr,"IP Address 1 ") and check_error_in_stderr(bun_stderr,"IP Address 1 "):
                        move = True

                    elif check_error_in_stderr(deno_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"that shadows a"):
                        move = True

                    elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True

                    elif check_error_in_stderr(deno_stderr,"") and check_error_in_stderr(bun_stderr,""):
                        move = True  

                    elif deno_stderr == bun_stderr:
                        move = True 

                    elif check_error_in_stderr(bun_stderr,"Full Path") and check_error_in_stderr(deno_stderr,"Full Path"):
                        move = True 

                    elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin/bash") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin/bash"):
                        move = True 

                    if move and "low_level_filter_48" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_48"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_48"] += 1

            #low level filter 49
            if check_error_in_stderr(node_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"SyntaxError: "):
                if check_error_in_stderr(node_stderr,"Illegal 'use strict' directive in function") and check_error_in_stderr(deno_stderr,"Illegal 'use strict' directive in function"):
                    if bun_stderr == "":
                        move = True 

                        if "low_level_filter_49" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_49"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_49"] += 1 

            #low level filter 50
            if (check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"message: ''")) or check_error_in_stderr(node_stderr,"accessed !== true") or check_error_in_stderr(node_stderr,"Cannot set properties of undefined") or check_error_in_stderr(node_stderr,"testResult !== true") or check_error_in_stderr(node_stderr,"TypeError: Cannot convert undefined or null to object") or check_error_in_stderr(node_stderr,"Should define own properties") or check_error_in_stderr(node_stderr,"f.apply(undefined) !== true") or check_error_in_stderr(node_stderr,"f.call() !== true") or check_error_in_stderr(node_stderr,"f.apply(undefined) !== true") or check_error_in_stderr(node_stderr,"f.apply() !== true") or check_error_in_stderr(node_stderr,"f.bind(null)() !== true") or check_error_in_stderr(node_stderr,"f.call(null) !== true") or check_error_in_stderr(node_stderr,"f.bind(undefined)() !== true") or check_error_in_stderr(node_stderr,"'Expected true but got false'") or check_error_in_stderr(node_stderr,"f1() !== true") or check_error_in_stderr(node_stderr,"f.call(undefined) !== true") or (check_error_in_stderr(node_stderr,"Expected SameValue") and check_error_in_stderr(node_stderr,"to be true")):
                if deno_stderr == bun_stderr:
                    move = True
                elif check_error_in_stderr(deno_stderr,"has already been declared") and (check_error_in_stderr(bun_stderr,"that shadows a ") or check_error_in_stderr(bun_stderr,"No such file or directory") or check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"Full Path: ") or check_error_in_stderr(bun_stderr,"Current HOME Directory") or check_error_in_stderr(bun_stderr,"Full Path: ") or check_error_in_stderr(bun_stderr,"subprocess forked") or check_error_in_stderr(bun_stderr,"Response: ") or check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin") or check_error_in_stderr(bun_stderr,"is not an object")):
                    move = True
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/") and check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin/bash") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin/bash"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"No such file or directory") and check_error_in_stderr(bun_stderr,"No such file or directory"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                    if check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"IP Address 1: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True 

                    if move and "low_level_filter_50" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_50"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_50"] += 1

                elif check_error_in_stderr(deno_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"TypeError: "):
                    if check_error_in_stderr(deno_stderr,"Cannot set") and check_error_in_stderr(deno_stderr,"which has only a getter") and check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                        move = True 

                    if move and "low_level_filter_50" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_50"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_50"] += 1

                elif check_error_in_stderr(deno_stderr,"Uncaught (in promise) "):
                    if check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"IP Address 1: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"TypeError: Attempted to assign to readonly property"):
                        move = True

                    if move and "low_level_filter_50" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_50"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_50"] += 1

            #low level filter 51
            if check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                if deno_stderr == "":
                    move = True

                    if "low_level_filter_51" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_51"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_51"] += 1

            #low level filter 52
            if check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                if check_error_in_stderr(node_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True 
                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"TypeError: Assignment to constant variable") and check_error_in_stderr(bun_stderr,"assignment will throw because") and check_error_in_stderr(bun_stderr,"is a constant"):
                    move = True 
                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"is not an object") and check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"is not an object"):
                    move = True 
                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"is not a constructor") and check_error_in_stderr(bun_stderr,"is not a constructor"):
                    move = True
                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1 
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1 
                elif check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True
                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"root:x:0:0:root:") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                    move = True
                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"Expected a RangeError but got a Test262Error") and check_error_in_stderr(bun_stderr,"Expected a RangeError but got a Test262Error"):
                    move = True
                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"is not callable") and check_error_in_stderr(bun_stderr,"is not callable"):
                    move = True 
                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"RangeError: ") and check_error_in_stderr(node_stderr,"Invalid code point "):
                    if check_error_in_stderr(bun_stderr,"TypeError: Attempted to assign to readonly property"):
                        move = True 
                        if move and "low_level_filter_52" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_52"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"which is not a string") and check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"includes non String"):
                    move = True 

                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"but found"):
                    if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin") or check_error_in_stderr(node_stderr,"Server running at") or check_error_in_stderr(node_stderr,"Current HOME Directory") or check_error_in_stderr(node_stderr,"Response: ") or check_error_in_stderr(node_stderr,"IP Address 1: ") or check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True 

                        if move and "low_level_filter_52" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_52"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"TypeError: Cannot redefine property"):
                    if check_error_in_stderr(bun_stderr,"TypeError: Attempting to change") and check_error_in_stderr(bun_stderr,"of an unconfigurable property."):
                        move = True 

                        if move and "low_level_filter_52" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_52"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"object is not extensible"):
                    if check_error_in_stderr(bun_stderr,"TypeError: Attempting to define") and check_error_in_stderr(bun_stderr,"that is not extensible"):
                        move = True 

                        if move and "low_level_filter_52" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_52"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_52"] += 1
                elif check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"is not a function"):
                    if check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"is not a function"):
                        move = True 

                        if move and "low_level_filter_52" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_52"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_52"] += 1
                
                elif check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"Expected a ") and check_error_in_stderr(bun_stderr,"but no exception was thrown at all"):
                    if check_error_in_stderr(node_stderr,"SyntaxError: ") and check_error_in_stderr(node_stderr,"has already been declared"): 
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Full Path: ") or check_error_in_stderr(node_stderr,"Current HOME Directory: ") or check_error_in_stderr(node_stderr,"IP Address 1: ") or check_error_in_stderr(node_stderr,"subprocess forked") or check_error_in_stderr(node_stderr,"Server running at") or check_error_in_stderr(node_stderr,"Response: ") or check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 

                        if move and "low_level_filter_52" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_52"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_52"] += 1

                elif check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"of empty array with no initial value"):
                    if check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"of empty array with no initial value"):
                        move = True 

                        if move and "low_level_filter_52" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_52"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_52"] += 1

                elif check_error_in_stderr(node_stderr,"ERR_INVALID_ARG_TYPE"):
                    if check_error_in_stderr(bun_stderr,"Response: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True

                    if move and "low_level_filter_52" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_52"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_52"] += 1



                

            #low level filter 53
            if check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                if check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True 
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"Response: "):
                    move = True

                    if move and "low_level_filter_53" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_53"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_53"] += 1

            #low level filter 54
            if check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                if node_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"BunOutput.txt") and check_error_in_stderr(bun_stderr,"no such file or directory"):
                    move = True

                    if move and "low_level_filter_54" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_54"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_54"] += 1

            #low level filter 55
            if check_error_in_stderr(node_stderr,"TypeError: "):
                if check_error_in_stderr(node_stderr,"Cannot set") and check_error_in_stderr(node_stderr,"which has only a getter"):
                    if "//wsl.localhost/Ubuntu-24.04/root/node-deno-bun/fuzz/testFuzz\n\n" == deno_stderr:
                        if "\\\\wsl.localhost\\Ubuntu-24.04\\root\\node-deno-bun\\fuzz\\testFuzz\n\n" == bun_stderr:
                            move = True 

                            if "low_level_filter_55" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_55"] = 1
                            else:
                               low_level_filter_counts["low_level_filter_55"] += 1

                    elif check_error_in_stderr(deno_stderr,"No such file or directory (os error ") and check_error_in_stderr(bun_stderr,"error: No such file or directory"):
                        move = True

                        if "low_level_filter_55" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_55"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_55"] += 1 
                    
                    elif check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared"):
                        if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"that shadows a") or check_error_in_stderr(bun_stderr,"Response: ") or check_error_in_stderr(bun_stderr,"Full Path: ") or check_error_in_stderr(bun_stderr,"Current HOME Directory: ") or check_error_in_stderr(bun_stderr,"Server running at") or check_error_in_stderr(bun_stderr,"subprocess forked"):
                            move = True 

                            if "low_level_filter_55" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_55"] = 1
                            else:
                               low_level_filter_counts["low_level_filter_55"] += 1

                    elif check_error_in_stderr(deno_stderr,"is not a function"):
                        if check_error_in_stderr(bun_stderr,"Full Path"):
                            move = True 
                        elif check_error_in_stderr(bun_stderr,"Response: "):
                            move = True 
                        elif check_error_in_stderr(bun_stderr,"Server running at"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"IP Address 1"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                            move = True

                        if move and "low_level_filter_55" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_55"] = 1
                        else:
                           if move:
                            low_level_filter_counts["low_level_filter_55"] += 1 

                    elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True 

                        if "low_level_filter_55" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_55"] = 1
                        else:
                           low_level_filter_counts["low_level_filter_55"] += 1

                    elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                        move = True 

                        if "low_level_filter_55" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_55"] = 1
                        else:
                           low_level_filter_counts["low_level_filter_55"] += 1



                    elif check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "): 
                        if check_error_in_stderr(bun_stderr,"IP Address 1: ") or check_error_in_stderr(bun_stderr,"Response: ") or check_error_in_stderr(bun_stderr,"Current HOME Directory") or check_error_in_stderr(bun_stderr,"Server running at") or check_error_in_stderr(bun_stderr,"subprocess forked") or check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin/bash") or check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                            move = True 

                        elif check_error_in_stderr(bun_stderr,"no such file or directory"):
                            move = True 

                        if move and "low_level_filter_55" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_55"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_55"] += 1

                    elif check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                        if check_error_in_stderr(deno_stderr,"Full Path"):
                            move = True 
                        elif check_error_in_stderr(deno_stderr,"Response: "):
                            move = True 
                        elif check_error_in_stderr(deno_stderr,"Server running at"):
                            move = True
                        elif check_error_in_stderr(deno_stderr,"subprocess forked"):
                            move = True
                        elif check_error_in_stderr(deno_stderr,"Current HOME Directory: "):
                            move = True
                        elif check_error_in_stderr(deno_stderr,"IP Address 1"):
                            move = True
                        elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")):
                            move = True

                        if move and "low_level_filter_55" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_55"] = 1
                        else:
                           if move:
                            low_level_filter_counts["low_level_filter_55"] += 1

                    elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin/bash"):
                        if check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin/bash"):
                            move = True 

                            if move and "low_level_filter_55" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_55"] = 1
                            else:
                                if move:
                                    low_level_filter_counts["low_level_filter_55"] += 1
                    
                    elif check_error_in_stderr(bun_stderr,"operation not permitted"):
                        if check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/root/node-deno-bun/fuzz/testFuzz\n\n"):
                            move = True 
                        elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin/bash") or check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709") or check_error_in_stderr(deno_stderr,"Current HOME Directory: ") or check_error_in_stderr(deno_stderr,"subprocess forked") or check_error_in_stderr(deno_stderr,"Server running at") or check_error_in_stderr(deno_stderr,"Full Path: ") or check_error_in_stderr(deno_stderr,"IP Address 1: "):
                            move = True 

                    elif check_error_in_stderr(deno_stderr,"Uncaught (in promise)"):
                        if check_error_in_stderr(bun_stderr,"Expected a ") and check_error_in_stderr(bun_stderr,"but got a"):
                            move = True 

                            if move and "low_level_filter_55" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_55"] = 1
                            else:
                                if move:
                                    low_level_filter_counts["low_level_filter_55"] += 1


            #low level filter 56
            if check_error_in_stderr(node_stderr,"has already been declared"):
                if check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True 

                    if "low_level_filter_56" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_56"] = 1
                    else:
                       low_level_filter_counts["low_level_filter_56"] += 1
                           
            #low levle filter 57
            if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"Test262Error"):
                msg1 = re.search(r"message: '(.*?)'", node_stderr, re.DOTALL)
                msg2 = re.search(r'message:\s*"(.*?)"', bun_stderr, re.DOTALL)
                if check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error") or check_error_in_stderr(deno_stderr,"Uncaught (in promise)") or check_error_in_stderr(deno_stderr,"has already been declared") or check_error_in_stderr(deno_stderr,"\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/mod.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/mod.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/mod.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/basename.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/constants.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/dirname.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/extname.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/format.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/from_file_url.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/is_absolute.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/join.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/normalize.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/parse.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/relative.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/resolve.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/to_file_url.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/to_namespaced_path.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/common.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_interface.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/glob_to_regexp.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/is_glob.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/join_globs.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/normalize_glob.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/basename.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/constants.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/dirname.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/extname.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/format.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/from_file_url.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/is_absolute.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/join.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/normalize.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/parse.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/relative.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/resolve.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/to_file_url.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/to_namespaced_path.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/common.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/glob_to_regexp.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/is_glob.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/join_globs.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/normalize_glob.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/basename.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/constants.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/dirname.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/extname.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/format.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/from_file_url.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/is_absolute.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/join.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/normalize.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/parse.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/relative.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/resolve.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/to_file_url.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/to_namespaced_path.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/common.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/glob_to_regexp.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/is_glob.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/join_globs.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/normalize_glob.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_os.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/common.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/basename.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/constants.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/strip_trailing_separators.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/windows/_util.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/dirname.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/assert_path.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/format.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/from_file_url.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/assert/assert.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/normalize.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/normalize_string.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/relative.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/to_file_url.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/_common/glob_to_reg_exp.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/path/posix/_util.ts\n\u001b[0m\u001b[32mDownload\u001b[0m https://deno.land/std@0.224.0/assert/assertion_error.ts\n"):

                    if msg1 and msg1.group(1) in bun_stderr:
                        move = True 

                        if "low_level_filter_57" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_57"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_57"] += 1

                    
                    if msg2 and msg2.group(1) in node_stderr:
                        move = True

                        if "low_level_filter_57" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_57"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_57"] += 1
                
                elif check_error_in_stderr(deno_stderr,"The module's source code could not be parsed") and check_error_in_stderr(deno_stderr,"Unexpected token") or check_error_in_stderr(deno_stderr,"Uncaught (in promise)"):
                    msg = re.search(r"message: '(.*?)'", node_stderr, re.DOTALL)
                    if msg and msg.group(1) in bun_stderr:
                        move = True 

                        if "low_level_filter_57" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_57"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_57"] += 1

                elif check_error_in_stderr(deno_stderr,"has already been declared"):
                    msg = re.search(r"message: '(.*?)'", node_stderr, re.DOTALL)
                    if msg and msg.group(1) in bun_stderr:
                        move = True 

                        if "low_level_filter_57" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_57"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_57"] += 1

            #low level filter 58
            if check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error"):
    
                if "low_level_filter_58" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_58"] = 1
                else:
                    low_level_filter_counts["low_level_filter_58"] += 1

                #filter75
                if check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True 

                    if "filter_75" not in filter_counts:
                        filter_counts["filter_75"] = 1
                    else:
                        filter_counts["filter_75"] += 1

                #filter76
                if check_error_in_stderr(node_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"has already been declared"):
                    move = True 

                    if "filter_76" not in filter_counts:
                        filter_counts["filter_76"] = 1
                    else:
                        filter_counts["filter_76"] += 1                    

                #filter77
                if check_error_in_stderr(node_stderr,"Expected a ") and check_error_in_stderr(node_stderr,"to be thrown but no exception was thrown at all") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True 

                    if "filter_77" not in filter_counts:
                        filter_counts["filter_77"] = 1
                    else:
                        filter_counts["filter_77"] += 1

                #filter78
                if check_error_in_stderr(node_stderr,"Expected a ") and check_error_in_stderr(node_stderr,"to be thrown but no exception was thrown at all") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True

                    if "filter_78" not in filter_counts:
                        filter_counts["filter_78"] = 1
                    else:
                        filter_counts["filter_78"] += 1

                #filter79
                if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True 

                    if "filter_79" not in filter_counts:
                        filter_counts["filter_79"] = 1
                    else:
                        filter_counts["filter_79"] += 1
                    
                #filter80
                if check_error_in_stderr(node_stderr,"Cannot set") and check_error_in_stderr(node_stderr,"which has only a getter") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True

                    if "filter_80" not in filter_counts:
                        filter_counts["filter_80"] = 1
                    else:
                        filter_counts["filter_80"] += 1

                #filter81
                if check_error_in_stderr(node_stderr,"/c/Windows\n\n") and check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\root\\node-deno-bun\\fuzz\\testFuzz\n\n"):
                    move = True 

                    if "filter_81" not in filter_counts:
                        filter_counts["filter_81"] = 1
                    else:
                        filter_counts["filter_81"] += 1

                
                
            #low level filter 59
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"TypeError: "):
                if check_error_in_stderr(node_stderr,"Cannot assign to read only property") and check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                    if check_error_in_stderr(deno_stderr,"oot:x:0:0:root:"):
                        move = True 

                        if "low_level_filter_59" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_59"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_59"] += 1

            #low level filter 60
            if check_error_in_stderr(node_stderr,"Fatal process out of memory") and check_error_in_stderr(deno_stderr,"Fatal process out of memory"):
                if check_error_in_stderr(bun_stderr,"error OutOfMemory"): 
                    move = True 

                    if "low_level_filter_60" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_60"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_60"] += 1

            #low level filter 61
            if check_error_in_stderr(bun_stderr,"Expected a ReferenceError ") and check_error_in_stderr(bun_stderr,"but no exception was thrown at all"):
                if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")):
                    move = True 

                    if "low_level_filter_61" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_61"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_61"] += 1
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(node_stderr,"<HTML>") and check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"<HTML>"):
                    move = True 

                    if "low_level_filter_61" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_61"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_61"] += 1

                elif check_error_in_stderr(node_stderr,"Current HOME Directory: ") and check_error_in_stderr(deno_stderr,"Current HOME Directory: "):
                    move = True 

                    if "low_level_filter_61" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_61"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_61"] += 1

                elif node_stderr == deno_stderr:
                    move = True 

                    if "low_level_filter_61" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_61"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_61"] += 1

                elif check_error_in_stderr(node_stderr,"/c/Windows\n\n"):
                    if check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/root/node-deno-bun/fuzz/testFuzz\n\n"):
                        move = True

                        if "low_level_filter_61" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_61"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_61"] += 1

                elif check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(deno_stderr,"Server running at"):
                    move = True 

                    if "low_level_filter_61" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_61"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_61"] += 1

                elif check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(node_stderr,"Full Path: ") or check_error_in_stderr(node_stderr,"IP Address 1: ") or check_error_in_stderr(node_stderr,"Current HOME Directory") or check_error_in_stderr(node_stderr,"Server running at") or check_error_in_stderr(node_stderr,"subprocess forked") or check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(node_stderr,"Response: "):
                        move = True 

                        if "low_level_filter_61" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_61"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_61"] += 1


            #low level filter 62
            if check_error_in_stderr(node_stderr,"/c/Windows") and check_error_in_stderr(node_stderr,"Response: "):
                if (check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04") and check_error_in_stderr(deno_stderr,"Response: ")) or check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04"):
                    if (check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04") and check_error_in_stderr(bun_stderr,"Response: ")) or check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04"):
                        move = True 

                        if "low_level_filter_62" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_62"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_62"] += 1

            #low level filter 63
            if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                if check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True 

                    if "low_level_filter_63" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_63"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_63"] += 1

            #low level filter 64
            if check_error_in_stderr(deno_stderr,"ReferenceError: ") and check_error_in_stderr(bun_stderr,"ReferenceError: "):
                if check_error_in_stderr(deno_stderr,"is not defined") and check_error_in_stderr(bun_stderr,"Can't find variable"):
                    if check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(node_stderr,"<HTML>"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:"):
                        move = True 

                    if move and "low_level_filter_64" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_64"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_64"] += 1

            #low level filter 65
            if check_error_in_stderr(node_stderr,"/c/Windows\n\n"):
                if check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\root\\node-deno-bun\\fuzz\\testFuzz\n\n"):
                        move = True 

                        if "low_level_filter_65" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_65"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_65"] += 1
                    
                    elif  check_error_in_stderr(bun_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"that shadows a"):
                        move = True 

                        if "low_level_filter_65" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_65"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_65"] += 1

            #low level filter 66
            if node_stderr == "Res" or node_stderr == "Response: <HT":
                if check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"<HTML>"):
                    if check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                        move = True 

                        if "low_level_filter_66" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_66"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_66"] += 1

            #low level filter 67
            if check_error_in_stderr(node_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                if check_error_in_stderr(deno_stderr,"ReferenceError: ") and check_error_in_stderr(deno_stderr,"is not defined"):
                    move = True 

                    if "low_level_filter_67" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_67"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_67"] += 1

            #low level filter 68
            if check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Expected a ") and check_error_in_stderr(bun_stderr,"but got a "):
                if check_error_in_stderr(deno_stderr,"Expected a ") and check_error_in_stderr(deno_stderr,"but got a "):
                    move = True 

                    if "low_level_filter_68" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_68"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_68"] += 1

            #low level filter 69
            if check_error_in_stderr(node_stderr,"Expected a") and check_error_in_stderr(node_stderr,"but no exception was thrown at all"):
                if check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/root/node-deno-bun/fuzz/testFuzz"):
                    if check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\root\\node-deno-bun\\fuzz\\testFuzz"):
                        move = True 
                elif check_error_in_stderr(bun_stderr,"operation not permitted"):
                    if check_error_in_stderr(deno_stderr,"Response: ") or check_error_in_stderr(deno_stderr,"Full Path: ") or check_error_in_stderr(deno_stderr,"IP Address 1: ") or check_error_in_stderr(deno_stderr,"subprocess forked") or check_error_in_stderr(deno_stderr,"Current HOME Directory: ") or check_error_in_stderr(deno_stderr,"Server running at") or check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 
                elif check_error_in_stderr(deno_stderr,"Server running at"):
                    if check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True
                elif check_error_in_stderr(deno_stderr,"Response: "):
                    if check_error_in_stderr(bun_stderr,"Response: "):
                        move = True 
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"The system cannot find the file specified"):
                    if check_error_in_stderr(bun_stderr,"Current HOME Directory:"): 
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"IP Address 1"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 

                elif deno_stderr == bun_stderr:
                    move = True 

                if move and "low_level_filter_69" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_69"] = 1
                else:
                    if move:       
                        low_level_filter_counts["low_level_filter_69"] += 1
            
            if check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(node_stderr,"has already been declared"):
                if check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/root/node-deno-bun/fuzz/testFuzz"):
                    if check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\root\\node-deno-bun\\fuzz\\testFuzz"):
                        move = True 

                        if "low_level_filter_69" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_69"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_69"] += 1
                
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True 

                    if "low_level_filter_69" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_69"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_69"] += 1

            #low level filter 70
            if check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                if check_error_in_stderr(deno_stderr,"The system cannot find the file specified"):
                    if check_error_in_stderr(bun_stderr,"no such file or directory"):
                        move =  True 

                        if "low_level_filter_70" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_70"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_70"] += 1

            #low level filter 71
            if check_error_in_stderr(node_stderr,"ReferenceError: "):
                if check_error_in_stderr(node_stderr,"is not defined"):
                    if check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"<HTML>"):
                        if check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                            move = True 
                            
                            if "low_level_filter_71" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_71"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_71"] += 1
                    
                    elif check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error ") and check_error_in_stderr(bun_stderr,"Can't find variable"):
                        move = True 

                        if "low_level_filter_71" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_71"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_71"] += 1

                    elif check_error_in_stderr(deno_stderr,"No such file or directory (os error "):
                        if check_error_in_stderr(bun_stderr,"No such file or directory"):
                            move = True 

                            if "low_level_filter_71" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_71"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_71"] += 1

            #low level filter 72
            if check_error_in_stderr(node_stderr,"TypeError: "):
                if (check_error_in_stderr(node_stderr,"Cannot set properties of ") or check_error_in_stderr(node_stderr,"is not iterable")) and (check_error_in_stderr(deno_stderr,"has already been declared") or check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error ")):
                    if check_error_in_stderr(bun_stderr,"is not an object") or check_error_in_stderr(bun_stderr,"is not a function") or check_error_in_stderr(bun_stderr,"that shadows a "):
                        move = True 

                        if "low_level_filter_72" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_72"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_72"] += 1

            #low level filter 73
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"TypeError: "):
                if check_error_in_stderr(node_stderr,"is not iterable") and (check_error_in_stderr(deno_stderr,"has already been declared") or check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error ")):
                    if check_error_in_stderr(bun_stderr,"is not an object"):
                        move = True 

                        if "low_level_filter_73" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_73"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_73"] += 1

                elif check_error_in_stderr(node_stderr,"is not iterable") and check_error_in_stderr(deno_stderr,"not enough space on the disk. (os error ") and check_error_in_stderr(bun_stderr,"is not an object"):
                    move = True 

                    if "low_level_filter_73" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_73"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_73"] += 1

            #low level filter 74
            if check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                if check_error_in_stderr(node_stderr,"/c/Windows") and check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/") and check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                    move = True 

                    if "low_level_filter_74" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_74"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_74"] += 1

            #low level filter 75
            if check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(node_stderr,"IP Address 1: "):
                if check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True 

                    if "low_level_filter_75" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_75"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_75"] += 1

            #low level filter 76
            if check_error_in_stderr(node_stderr,"Current HOME Directory: ") and check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                move = True 

                if "low_level_filter_76" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_76"] = 1
                else:
                    low_level_filter_counts["low_level_filter_76"] += 1

            #low level filter 77
            if node_stderr == deno_stderr:
                if check_error_in_stderr(bun_stderr,"no such file or directory"):
                    move = True 

                    if "low_level_filter_77" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_77"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_77"] += 1

            #low level filter 78
            if check_error_in_stderr(node_stderr,"ReferenceError: ") and check_error_in_stderr(node_stderr,"is not defined"):
                if check_error_in_stderr(deno_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True 

                    if "low_level_filter_78" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_78"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_78"] += 1

            #low level filter 79
            if node_stderr == "/c/Windows\n\n" or check_error_in_stderr(node_stderr,"is not a function") or check_error_in_stderr(node_stderr,"has already been declared"):
                if check_error_in_stderr(deno_stderr,"Unexpected token") and check_error_in_stderr(deno_stderr,"The module's source code could not be parsed:"):
                    if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"but found"):
                        move = True 

                        if "low_level_filter_79" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_79"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_79"] += 1
                    elif check_error_in_stderr(bun_stderr,"has already been declared"):
                        move = True 
                            
                        if "low_level_filter_79" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_79"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_79"] += 1

            #low level filter 80
            if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                if check_error_in_stderr(node_stderr,"/c/Windows") and check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/") and check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04"):
                    if check_error_in_stderr(node_stderr,"IP Address 1: ") and check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                        move = True 
                            
                        if "low_level_filter_80" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_80"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_80"] += 1

            #low level filter 81
            if check_error_in_stderr(node_stderr,"'this' had incorrect value"):
                if check_error_in_stderr(bun_stderr,"'this' had incorrect value"):
                    if check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared"):
                        move = True 
                    elif check_error_in_stderr(deno_stderr,"Response: "): 
                        move = True
                    elif check_error_in_stderr(deno_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 
                    elif check_error_in_stderr(deno_stderr,"'this' had incorrect value"):
                        move = True 

                        if "low_level_filter_81" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_81"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_81"] += 1

                elif deno_stderr == bun_stderr:
                    move = True 

                    if "low_level_filter_81" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_81"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_81"] += 1

                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"<HTML>"):
                    if check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                        move = True 

                        if "low_level_filter_81" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_81"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_81"] += 1

                elif check_error_in_stderr(deno_stderr,"Server running at"):
                    if check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True 

                        if "low_level_filter_81" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_81"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_81"] += 1

                elif check_error_in_stderr(deno_stderr,"IP Address 1: "):
                    if check_error_in_stderr(bun_stderr,"IP Address 1: "):
                        move = True 

                        if "low_level_filter_81" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_81"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_81"] += 1

                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 

                        if "low_level_filter_81" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_81"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_81"] += 1

                elif check_error_in_stderr(deno_stderr,"Full Path: "):
                    if check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True 

                        if "low_level_filter_81" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_81"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_81"] += 1

                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:"):
                    if check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                        move = True 

                        if "low_level_filter_81" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_81"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_81"] += 1 

                elif check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error"):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"Response: ") or check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True 

                        if "low_level_filter_81" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_81"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_81"] += 1

                elif check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"that shadows a"):
                        move = True 

                        if "low_level_filter_81" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_81"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_81"] += 1

                

            #low level filter 82
            if check_error_in_stderr(node_stderr,"root:x:0:0:root:"):
                if check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"that shadows a "):
                        move = True 

                        if "low_level_filter_82" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_82"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_82"] += 1

            #low level filter 83
            if check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                    if check_error_in_stderr(bun_stderr,"Current HOME Directory: ") and check_error_in_stderr(deno_stderr,"cannot find the file specified"):
                        move = True 

                        if "low_level_filter_83" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_83"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_83"] += 1

            #low level filter 84
            if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"SyntaxError: "):
                if check_error_in_stderr(node_stderr,"arrow function invoked exactly once") and check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"that shadows a "):
                        move = True 

                        if "low_level_filter_84" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_84"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_84"] += 1

            #low level filter 85
            if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                if check_error_in_stderr(node_stderr,"root:x:0:0:root:") and check_error_in_stderr(deno_stderr,"root:x:0:0:root:"):
                    move = True 

                    if "low_level_filter_85" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_85"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_85"] += 1

            #low level filter 86
            if check_error_in_stderr(node_stderr,"subprocess forked") and check_error_in_stderr(node_stderr,"subprocess killed"):
                if check_error_in_stderr(bun_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"SyntaxError: "):
                    if check_error_in_stderr(deno_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"that shadows a "):
                        move = True 

                        if "low_level_filter_86" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_86"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_86"] += 1

            #low level filter 87
            if check_error_in_stderr(deno_stderr,"TypeError: Cannot redefine property"):
                if node_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True 
                elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True 

                    if move and "low_level_filter_87" not in low_level_filter_counts:
                         low_level_filter_counts["low_level_filter_87"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_87"] += 1

            elif check_error_in_stderr(node_stderr,"TypeError: Cannot redefine property"):
                if check_error_in_stderr(deno_stderr,"Address already in use (os error ") and check_error_in_stderr(bun_stderr,"Failed to start server"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Attempting to change"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"that shadows a"):
                        move = True 
                elif check_error_in_stderr(deno_stderr,"Uncaught (in promise)"):
                    if check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Attempting to change"):
                        move = True 
                elif check_error_in_stderr(deno_stderr,"AddrInUse"):
                    if check_error_in_stderr(bun_stderr,"EADDRINUSE"):
                        move = True 

                    if move and "low_level_filter_87" not in low_level_filter_counts:
                         low_level_filter_counts["low_level_filter_87"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_87"] += 1

            #low level filter 88
            if check_error_in_stderr(node_stderr,"/c/Windows\n\n"):
                if check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/"):
                    if check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                        move = True 

                        if "low_level_filter_88" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_88"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_88"] += 1

            #low level filter 89
            if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                if (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True

                        if "low_level_filter_89" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_89"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_89"] += 1
                    elif check_error_in_stderr(bun_stderr,"operation not permitted"):
                        move = True 

                        if "low_level_filter_89" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_89"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_89"] += 1

            #low level filter 90
            if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"invoked exactly once"):
                if check_error_in_stderr(deno_stderr,"ReferenceError: ") and check_error_in_stderr(deno_stderr,"is not defined"):
                    if check_error_in_stderr(bun_stderr,"ReferenceError: ") and check_error_in_stderr(bun_stderr,"Can't find variable: "):
                        move = True 

                        if "low_level_filter_90" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_90"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_90"] += 1
                
                elif check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"that shadows a"):
                        move = True 

                        if "low_level_filter_90" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_90"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_90"] += 1

            #low level filter 91
            if check_error_in_stderr(bun_stderr,"operation not permitted"):
                if check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                    move = True 
                if deno_stderr == node_stderr:
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(node_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(node_stderr,"subprocess forked"): 
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(node_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(node_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(node_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                    move = True 
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(node_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"PermissionDenied: Access is denied. (os error "):
                    if check_error_in_stderr(node_stderr,"Server running at"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True 


                    if move and "low_level_filter_91" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_91"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_91"] += 1

            #low level filter 92
            if check_error_in_stderr(node_stderr,"Client code can adversely affect behavior"):
                if check_error_in_stderr(deno_stderr,"root:x:0:0:root:") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/") and check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                    move = True 
                elif deno_stderr == bun_stderr:
                    move = True 

                    if move and "low_level_filter_92" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_92"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_92"] += 1

            #low level filter 93
            if check_error_in_stderr(deno_stderr,"The module's source code could not be parsed") and check_error_in_stderr(deno_stderr,"Unexpected token"):
                if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"but found"):
                    if check_error_in_stderr(node_stderr,"root:x:0:0:root:"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                        move = True
                elif check_error_in_stderr(bun_stderr,"operation not permitted"):
                    if check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                        move = True 

                if move and "low_level_filter_93" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_93"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_93"] += 1

            #low level filter 94
            if check_error_in_stderr(deno_stderr,"The module's source code could not be parsed") and check_error_in_stderr(deno_stderr,"Unexpected token"):
                if check_error_in_stderr(node_stderr,"root:x:0:0:root:") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3")  and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True
                elif node_stderr == bun_stderr:
                    move = True 

                if move and "low_level_filter_94" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_94"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_94"] += 1

            #low level filter 95
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"Cannot destructure"):
                if deno_stderr == bun_stderr:
                    move = True
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                    move = True
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709"))  and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"<HTML>") and check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/") and check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:"):
                    move = True 

                if move and "low_level_filter_95" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_95"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_95"] += 1
                
            #low level filter 96
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"Cannot assign to read only property"):
                if deno_stderr == bun_stderr:
                    move = True
                elif check_error_in_stderr(deno_stderr,"Uncaught (in promise)"):
                    if check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"Expected SameValue") and check_error_in_stderr(bun_stderr,"to be true"):
                        move = True 
                elif check_error_in_stderr(deno_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz") and check_error_in_stderr(bun_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                    move = True
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709"))  and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"<HTML>") and check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/") and check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                    if check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                        move = True
                elif (check_error_in_stderr(deno_stderr,"No such file or directory") or check_error_in_stderr(deno_stderr,"(os error 2)")) and check_error_in_stderr(bun_stderr,"No such file or directory"):
                    move = True 


                if move and "low_level_filter_96" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_96"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_96"] += 1

            #low level filter 97
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(deno_stderr,"SyntaxError: "):
                if check_error_in_stderr(node_stderr,"which has only a getter") and check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property."):
                        move = True

                    if move and "low_level_filter_97" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_97"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_97"] += 1

            #low level filter 98
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"is not a function"):
                if check_error_in_stderr(deno_stderr,"root:x:0:0:root:") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                    move = True
                elif check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"is not a function"):
                    if check_error_in_stderr(deno_stderr,"Uncaught (in promise) "):
                        move = True 
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True
                elif (check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"<HTML>")) and (check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>")):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/") and check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True 
                elif deno_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True 

                if move and "low_level_filter_98" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_98"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_98"] += 1

            #low level filter 99
            if check_error_in_stderr(node_stderr,"Full Path: \\etc\\passwd\n"):
                if check_error_in_stderr(deno_stderr,"Full Path: \\etc\\passwd\n"):
                    if check_error_in_stderr(bun_stderr,"Full Path: \\etc\\passwd\n"):
                        move = True 

                        if "low_level_filter_99" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_99"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_99"] += 1

            #low level filter 100
            if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                if check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                    if check_error_in_stderr(bun_stderr,"that shadows a "):
                        move = True 

                        if "low_level_filter_100" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_100"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_100"] += 1

            #low level filter 101
            if check_error_in_stderr(node_stderr,"ReferenceError: ") and check_error_in_stderr(node_stderr,"is not defined"):
                if check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/"):
                    if check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                        move = True 

                        if "low_level_filter_101" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_101"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_101"] += 1

                elif check_error_in_stderr(deno_stderr,"ReferenceError: ") and check_error_in_stderr(deno_stderr,"is not defined"):
                    if bun_stderr is None:
                        move = True 

                        if "low_level_filter_101" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_101"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_101"] += 1


            #low level filter 102
            if check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"undefined is not a function"):
                if node_stderr == deno_stderr:
                    move = True 
                elif check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(deno_stderr,"Full Path: "):
                    move = True
                if check_error_in_stderr(node_stderr,"Current HOME Directory: ") and check_error_in_stderr(deno_stderr,"Current HOME Directory: "):
                    move = True
                if (check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(node_stderr,"<HTML>")) and (check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(deno_stderr,"<HTML>")):
                    move = True 

                if move and "low_level_filter_102" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_102"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_102"] += 1    

            #low level filter 103
            if check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared") and bun_stderr == "":
                if check_error_in_stderr(node_stderr,"ReferenceError: ") and check_error_in_stderr(node_stderr,"port is not defined"):
                    move = True
                if check_error_in_stderr(node_stderr,"ReferenceError: ") and check_error_in_stderr(node_stderr,"spawn is not defined"):
                    move = True
                if check_error_in_stderr(node_stderr,"Expected a ") and check_error_in_stderr(node_stderr,"but no exception was thrown at all"):
                    move = True 

                if move and "low_level_filter_103" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_103"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_103"] += 1  

            #low level filter 104
            if deno_stderr == bun_stderr:
                if check_error_in_stderr(node_stderr,"IP Address 1: "):
                    move = True 
                elif check_error_in_stderr(node_stderr,"ReferenceError: ") and check_error_in_stderr(node_stderr,"port is not defined"):
                    move = True 
                elif check_error_in_stderr(node_stderr,"SyntaxError: ") and check_error_in_stderr(node_stderr,"has already been declared"):
                    move = True 
                elif node_stderr == "/c/Windows\n\n":
                    move = True 

                if move and "low_level_filter_104" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_104"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_104"] += 1

            #low level filter 105
            if bun_stderr == "" or bun_stderr is None:
                if check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(node_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(node_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(node_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(node_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(node_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True  
                elif (check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared")) or check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                    if check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True 

                if move and "low_level_filter_105" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_105"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_105"] += 1

            #low level filter 106
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"Cannot read properties of undefined"):
                if check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                        move = True

                    if move and "low_level_filter_106" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_106"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_106"] += 1

                elif bun_stderr == deno_stderr:
                    move = True 
                elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")):
                    move = True 
                elif check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>") and check_error_in_stderr(deno_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\") and check_error_in_stderr(deno_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                    move = True
                elif check_error_in_stderr(bun_stderr,"subprocess forked") and check_error_in_stderr(deno_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(bun_stderr,"Full Path: ") and check_error_in_stderr(deno_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(bun_stderr,"root:x:0:0:root:") and check_error_in_stderr(deno_stderr,"root:x:0:0:root:"):
                    move = True
                elif check_error_in_stderr(bun_stderr,"Server running at") and check_error_in_stderr(deno_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"cannot be destructured"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"that shadows a "):
                        move = True 

                if move and "low_level_filter_106" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_106"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_106"] += 1

            #low level filter 107
            if check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                if check_error_in_stderr(bun_stderr,"no such file or directory"):
                    if check_error_in_stderr(node_stderr,"Current HOME Directory"):
                        move = True 

                        if "low_level_filter_107" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_107"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_107"] += 1

            #low level filter 108
            if check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared"):
                if check_error_in_stderr(bun_stderr,"no such file or directory"):
                    if check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                        move = True 

                    elif check_error_in_stderr(node_stderr,"ReferenceError: ") and check_error_in_stderr(node_stderr,"is not defined"):
                        move = True 

                elif node_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(node_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(node_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True 

                if move and "low_level_filter_108" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_108"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_108"] += 1


            #low level filter 109
            if check_error_in_stderr(bun_stderr,"Expected a ReferenceError but got a Test262Error"):
                if node_stderr == deno_stderr:
                    move = True 

                    if "low_level_filter_109" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_109"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_109"] += 1

            #low level filter 110
            if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"message: ''"):
                if bun_stderr == deno_stderr:
                    move = True
                elif check_error_in_stderr(deno_stderr,"has already been declared") and check_error_in_stderr(bun_stderr,"that shadows a"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Server running at ") and check_error_in_stderr(bun_stderr,"Server running at "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"The system cannot find the file specified") and check_error_in_stderr(bun_stderr,"no such file or directory"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"//wsl.localhost/Ubuntu-24.04/") and check_error_in_stderr(bun_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                    move = True  

                if move and "low_level_filter_110" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_110"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_110"] += 1

            #low level filter 111
            if check_error_in_stderr(node_stderr,"Full Path: /etc/passwd\n"):
                if check_error_in_stderr(deno_stderr,"Full Path: /etc/passwd\n"):
                    if check_error_in_stderr(bun_stderr,"Full Path: /etc/passwd\n"):
                        move = True 

                        if "low_level_filter_111" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_111"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_111"] += 1

            #low level filter 112
            if check_error_in_stderr(node_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz\n\n"):
                if check_error_in_stderr(deno_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz\n\n"):
                    if check_error_in_stderr(bun_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz\n\n"):
                        move = True 

                        if "low_level_filter_112" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_112"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_112"] += 1

            #low level filter 113
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"TypeError: "):
                if check_error_in_stderr(node_stderr,"Cannot destructure property"):
                    if check_error_in_stderr(deno_stderr,"has already been declared"):
                        if check_error_in_stderr(bun_stderr,"cannot be destructured"):
                            move = True 

                            if "low_level_filter_113" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_113"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_113"] += 1

            #low level filter 114
            if check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                
                if check_error_in_stderr(bun_stderr,"ReferenceError: ") and check_error_in_stderr(bun_stderr,"Can't find variable"):
                    if check_error_in_stderr(node_stderr,"IP Address 1"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:"):
                        move = True        
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                            
                    if move and "low_level_filter_114" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_114"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_114"] += 1
                

                elif check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"are proper instances of GeneratorFunction"):
                    if check_error_in_stderr(node_stderr,"Full Path: ") or check_error_in_stderr(node_stderr,"IP Address 1") or check_error_in_stderr(node_stderr,"Response: ") or check_error_in_stderr(node_stderr,"Current HOME Directory") or check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin") or check_error_in_stderr(node_stderr,"subprocess forked") or check_error_in_stderr(node_stderr,"Server running at") or check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 

                elif check_error_in_stderr(node_stderr,"SyntaxError: ") and check_error_in_stderr(node_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"IP Address 1"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                        move = True   
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                        move = True   
                    elif check_error_in_stderr(bun_stderr,"no such file or directory"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"Expected SameValue") and check_error_in_stderr(bun_stderr,"to be true"):
                        move = True 
                        

                elif check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"should match"):
                    if check_error_in_stderr(bun_stderr,"TypeError: Attempted to assign to readonly property"):
                        move = True 

                elif check_error_in_stderr(bun_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"that shadows a"):
                    if check_error_in_stderr(node_stderr,"IP Address 1"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"\\\\wsl.localhost\\Ubuntu-24.04\\"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:"):
                        move = True        
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True

                    if move and "low_level_filter_114" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_114"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_114"] += 1

                elif check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"Expected true but got false"):
                    if check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"IP Address 1"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True

                elif check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"function(){return 1} >= function(){return 1}"):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"Current HOME Directory") or check_error_in_stderr(bun_stderr,"Server running at") or check_error_in_stderr(bun_stderr,"IP Address 1") or check_error_in_stderr(bun_stderr,"Full Path") or check_error_in_stderr(bun_stderr,"subprocess forked") or check_error_in_stderr(bun_stderr,"Response: "):
                        move = True

                elif check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"Expected a ") and check_error_in_stderr(node_stderr,"but got a"):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"Current HOME Directory") or check_error_in_stderr(bun_stderr,"Server running at") or check_error_in_stderr(bun_stderr,"IP Address 1") or check_error_in_stderr(bun_stderr,"Full Path") or check_error_in_stderr(bun_stderr,"subprocess forked") or check_error_in_stderr(bun_stderr,"Response: "):
                        move = True

                elif check_error_in_stderr(node_stderr,"Assertion failed: "):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"Current HOME Directory") or check_error_in_stderr(bun_stderr,"Server running at") or check_error_in_stderr(bun_stderr,"IP Address 1") or check_error_in_stderr(bun_stderr,"Full Path") or check_error_in_stderr(bun_stderr,"subprocess forked") or check_error_in_stderr(bun_stderr,"Response: "):
                        move = True

                elif check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"invalid access") and check_error_in_stderr(node_stderr,"Expected a") and check_error_in_stderr(node_stderr,"but got a"):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"Current HOME Directory") or check_error_in_stderr(bun_stderr,"Server running at") or check_error_in_stderr(bun_stderr,"IP Address 1") or check_error_in_stderr(bun_stderr,"Full Path") or check_error_in_stderr(bun_stderr,"subprocess forked") or check_error_in_stderr(bun_stderr,"Response: "):
                        move = True 

                elif check_error_in_stderr(bun_stderr,"error: undefined"):
                    if check_error_in_stderr(node_stderr,"undefined") and check_error_in_stderr(node_stderr,"node --trace-uncaught"):
                        move = True

                elif check_error_in_stderr(node_stderr,"RangeError: ") and check_error_in_stderr(node_stderr,"Offset is outside the bounds "):
                    if check_error_in_stderr(bun_stderr,"RangeError: ") and check_error_in_stderr(bun_stderr,"out of bounds access"):
                        move = True 

                elif check_error_in_stderr(bun_stderr,"TypeError: Reduce of empty array with no initial value"):
                    if check_error_in_stderr(node_stderr,"TypeError: Reduce of empty array with no initial value"):
                        move = True

                elif check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"called on incompatible receiver"):
                    if check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Receiver should be a "):
                        move = True

                elif check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"which has only a getter"):
                    if check_error_in_stderr(node_stderr,"no such file or directory"):
                        move = True 

                elif check_error_in_stderr(node_stderr,"ReferenceError: ") and check_error_in_stderr(node_stderr,"is not defined"):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"IP Address 1"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                        move = True   
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                        move = True   
                    elif check_error_in_stderr(bun_stderr,"no such file or directory"):
                        move = True 

                    if move and "low_level_filter_114" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_114"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_114"] += 1  

            #low level filter 115
            if check_error_in_stderr(bun_stderr,"Expected a RangeError but got a Test262Error"):
                if check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(deno_stderr,"Server running at"):
                    move = True 
                elif node_stderr == deno_stderr:
                    move = True 

                if move and "low_level_filter_115" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_115"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_115"] += 1 

            #low level filter 116
            if check_error_in_stderr(node_stderr,"TypeError:") and check_error_in_stderr(deno_stderr,"TypeError:"):
                if check_error_in_stderr(node_stderr,"which has only a getter") and (check_error_in_stderr(deno_stderr,"which has only a getter") or check_error_in_stderr(deno_stderr,"is not a function")):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"IP Address 1"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True  
                    elif check_error_in_stderr(bun_stderr,"EADDRINUSE"):
                        move = True 

                elif check_error_in_stderr(node_stderr,"Assignment to constant variable") and check_error_in_stderr(deno_stderr,"Assignment to constant variable"):
                    if check_error_in_stderr(bun_stderr,"error: ") and check_error_in_stderr(bun_stderr,"is a constant"):
                        move = True 

                if move and "low_level_filter_116" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_116"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_116"] += 1

            #low level filter 117
            if check_error_in_stderr(node_stderr,"TypeError:") and check_error_in_stderr(node_stderr,"which has only a getter"):
                if check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"IP Address 1"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"<HTML>"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"root:x:0:0:root:"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                        move = True  

                    if move and "low_level_filter_117" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_117"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_117"] += 1

                            

            #low level filter 118
            if check_error_in_stderr(deno_stderr,"Expected a CustomError but got a Test262Error"):
                if check_error_in_stderr(node_stderr,"Server running at ") and check_error_in_stderr(bun_stderr,"Server running at "):
                    move = True

                    if "low_level_filter_118" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_118"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_118"] += 1

            #low level filter 119
            if check_error_in_stderr(node_stderr,"'testResult !== true'"):
                if check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"that shadows a"):
                        move = True 

                        if "low_level_filter_119" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_119"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_119"] += 1

            #low level filter 120
            if check_error_in_stderr(node_stderr,"Expected a RangeError but got a Test262Error"):
                if check_error_in_stderr(bun_stderr,"Expected a RangeError but got a Test262Error") and check_error_in_stderr(deno_stderr,"system cannot find the file specified. (os error "):
                    move = True

                    if "low_level_filter_120" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_120"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_120"] += 1

            #low level filter 121
            if check_error_in_stderr(node_stderr,"Test262Error"):
                if check_error_in_stderr(deno_stderr,"Uncaught (in promise)"):
                    if check_error_in_stderr(bun_stderr,"error: Failed to start server") or check_error_in_stderr(bun_stderr,"No such file or directory"):
                        move = True    

                        if "low_level_filter_121" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_121"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_121"] += 1 

                    elif check_error_in_stderr(bun_stderr,"TypeError: Attempted to assign to readonly property"):
                        if check_error_in_stderr(node_stderr,"should match"):
                            move = True 

                            if "low_level_filter_121" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_121"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_121"] += 1

                    elif check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"locale value must be a string or object"):
                        if check_error_in_stderr(node_stderr,"Expected a") and check_error_in_stderr(node_stderr,"but got a"):
                            move = True 

                            if "low_level_filter_121" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_121"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_121"] += 1

                    elif check_error_in_stderr(bun_stderr,"RangeError: ") and check_error_in_stderr(bun_stderr,"Maximum call stack size exceeded"):
                        if check_error_in_stderr(node_stderr,"Expeceted SameValue"):
                            move = True 

                            if "low_level_filter_121" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_121"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_121"] += 1

                    elif check_error_in_stderr(bun_stderr,"Expected a") and check_error_in_stderr(bun_stderr,"but got a"):
                        if check_error_in_stderr(node_stderr,"!== true"):
                            move = True 

                            if "low_level_filter_121" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_121"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_121"] += 1
            
    
                elif deno_stderr == bun_stderr:
                    move = True 

                    if "low_level_filter_121" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_121"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_121"] += 1


                elif check_error_in_stderr(deno_stderr,"No such file or directory (os error ") or check_error_in_stderr(deno_stderr,"The system cannot find the file specified. (os error "):
                    if check_error_in_stderr(bun_stderr,"No such file or directory"):
                        if check_error_in_stderr(node_stderr,"Expected a") and check_error_in_stderr(node_stderr,"but found a"):
                            move = True 

                        elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                            move = True 

                        elif check_error_in_stderr(node_stderr,"Response: "):
                            move = True 

                        elif check_error_in_stderr(node_stderr,"Full Path: "):
                            move = True

                        elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin/bash"):
                            move = True

                        elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                            move = True

                        if move and "low_level_filter_121" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_121"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_121"] += 1

                
                elif check_error_in_stderr(deno_stderr,"TypeError: ") and check_error_in_stderr(deno_stderr,"Cannot create property"):
                    if check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                        if check_error_in_stderr(node_stderr,"Expected SameValue"):
                            move = True 

                            if "low_level_filter_121" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_121"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_121"] += 1

                elif check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True 

                        if "low_level_filter_121" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_121"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_121"] += 1

                    elif check_error_in_stderr(bun_stderr,"that shadows a"):
                        move = True 

                        if "low_level_filter_121" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_121"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_121"] += 1

                    
                    elif check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"undefined is not an object "):
                        if check_error_in_stderr(node_stderr,"Expected SameValue"):
                            move = True 

                            if "low_level_filter_121" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_121"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_121"] += 1

                    
                    elif check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                        if check_error_in_stderr(node_stderr,"!== true"):
                            move = True 

                            if "low_level_filter_121" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_121"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_121"] += 1

                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        if check_error_in_stderr(node_stderr,"Expected a") and check_error_in_stderr(node_stderr,"but got a"):
                            move = True 

                            if "low_level_filter_121" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_121"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_121"] += 1

                    elif check_error_in_stderr(bun_stderr,"that shadows a"):
                        if check_error_in_stderr(node_stderr,"Expected SameValue"):
                            move = True 

                            if "low_level_filter_121" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_121"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_121"] += 1

                    elif check_error_in_stderr(bun_stderr,"error: No such file or directory"):
                        if check_error_in_stderr(node_stderr,"Expected SameValue"):
                            move = True 

                            if "low_level_filter_121" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_121"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_121"] += 1

                    elif check_error_in_stderr(deno_stderr,"subprocess forked"):
                        if check_error_in_stderr(bun_stderr,"subprocess forked"):
                            if check_error_in_stderr(node_stderr,"Expected SameValue"):
                                move = True 

                                if "low_level_filter_121" not in low_level_filter_counts:
                                    low_level_filter_counts["low_level_filter_121"] = 1
                                else:
                                    low_level_filter_counts["low_level_filter_121"] += 1

                    elif check_error_in_stderr(deno_stderr,"Response: "):
                        if check_error_in_stderr(bun_stderr,"Response: "):
                            if check_error_in_stderr(node_stderr,"Expected SameValue"):
                                move = True 

                                if "low_level_filter_121" not in low_level_filter_counts:
                                    low_level_filter_counts["low_level_filter_121"] = 1
                                else:
                                    low_level_filter_counts["low_level_filter_121"] += 1

                elif check_error_in_stderr(deno_stderr,"Server is up!"):
                    if check_error_in_stderr(bun_stderr,"Server is up!"):
                        if check_error_in_stderr(node_stderr,"Expected SameValue"):
                            move = True 

                            if "low_level_filter_121" not in low_level_filter_counts:
                                low_level_filter_counts["low_level_filter_121"] = 1
                            else:
                                low_level_filter_counts["low_level_filter_121"] += 1

                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin/bash"):
                    if check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin/bash"):
                        move = True 

                        if "low_level_filter_121" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_121"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_121"] += 1

            #low level fitler 122
            if check_error_in_stderr(node_stderr,"Response: <!doctype html>"):
                if check_error_in_stderr(deno_stderr,"Response: <!doctype html>"):
                    if check_error_in_stderr(bun_stderr,"Response: <!doctype html>"):
                        move = True 

                        if "low_level_filter_122" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_122"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_122"] += 1

            #low level filter 123
            if check_error_in_stderr(deno_stderr,"Uncaught (in promise)") and check_error_in_stderr(deno_stderr,"should match"):
                if check_error_in_stderr(node_stderr,"subprocess forked"):
                    if check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True 

                elif check_error_in_stderr(node_stderr,"Server running at"):
                    if check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True 

                elif check_error_in_stderr(node_stderr,"Response: "):
                    if check_error_in_stderr(bun_stderr,"Response: "):
                        move = True

                elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                    if check_error_in_stderr(bun_stderr,"IP Address 1: "):
                        move = True

                elif check_error_in_stderr(node_stderr,"Full Path: "):
                    if check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True

                elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 

                elif check_error_in_stderr(node_stderr,"ReferenceError: ") and check_error_in_stderr(node_stderr,"is not defined"):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"Full Path: ") or check_error_in_stderr(bun_stderr,"IP Address 1: ") or check_error_in_stderr(bun_stderr,"Response: ") or check_error_in_stderr(bun_stderr,"Current HOME Directory") or check_error_in_stderr(bun_stderr,"Server running at") or check_error_in_stderr(bun_stderr,"subprocess forked") or check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin/bash"):
                        move = True 


                if move and "low_level_filter_123" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_123"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_123"] += 1

            #low level filter 124
            if check_error_in_stderr(bun_stderr,"RangeError: ") and check_error_in_stderr(bun_stderr,"call stack"):
                if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    if (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")):    
                        move = True 

                        if "low_level_filter_124" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_124"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_124"] += 1

                elif deno_stderr == node_stderr:
                    move = True 

                    if "low_level_filter_124" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_124"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_124"] += 1

            #low level filter 125
            if check_error_in_stderr(deno_stderr,"Address already in use (os error "):
                if check_error_in_stderr(node_stderr,"Server running at"):
                    if check_error_in_stderr(bun_stderr,"error: Failed to start server"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"EADDRINUSE"):
                        move = True 

                elif check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"is not a function"):
                        if check_error_in_stderr(bun_stderr,"Failed to start server"):
                            move = True

                elif check_error_in_stderr(bun_stderr,"EADDRINUSE"):
                    if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"is not a function"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"is not defined"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"has already been declared"):
                        move = True 

                if move and "low_level_filter_125" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_125"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_125"] += 1

            #low level filter 126
            if check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"Test262Error"):
                
                msg = re.search(r'message:\s*"([^"]+)"', bun_stderr)
                if check_error_in_stderr(node_stderr,"has already been declared") or check_error_in_stderr(node_stderr,"Full Path: ") or check_error_in_stderr(node_stderr,"Response: ") or check_error_in_stderr(node_stderr,"Server running at") or check_error_in_stderr(node_stderr,"subprocess forked") or check_error_in_stderr(node_stderr,"Current HOME Directory") or check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(node_stderr,"TypeError: Cannot convert") or check_error_in_stderr(node_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz") or check_error_in_stderr(node_stderr,"is not defined"):
                    if msg and msg.group(1) in deno_stderr: 
                        move=True

                        if "low_level_filter_126" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_126"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_126"] += 1

            #low level filter 127
            if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                if check_error_in_stderr(deno_stderr,"TypeError: ") and check_error_in_stderr(deno_stderr," is not iterable"):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 

                        if "low_level_filter_127" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_127"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_127"] += 1

            #low level filter 128
            if check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                if check_error_in_stderr(deno_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"should match"):
                    move = True 

                    if "low_level_filter_128" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_128"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_128"] += 1

            #low level filter 129
            if check_error_in_stderr(deno_stderr,"Unexpected token"):
                if check_error_in_stderr(bun_stderr,"No such file or directory"):
                    if check_error_in_stderr(node_stderr,"Current HOME Directory: ") or check_error_in_stderr(node_stderr,"Response: ") or check_error_in_stderr(node_stderr,"Server running at") or check_error_in_stderr(node_stderr,"subprocess forked") or check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 

                        if "low_level_filter_129" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_129"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_129"] += 1


            #low level filter 130
            if check_error_in_stderr(deno_stderr,"has already been declared"):
                if check_error_in_stderr(bun_stderr,"Expected SameValue") and check_error_in_stderr(bun_stderr,"to be true"):
                    if check_error_in_stderr(node_stderr,"Current HOME Directory: ") or check_error_in_stderr(node_stderr,"Response: ") or check_error_in_stderr(node_stderr,"Server running at") or check_error_in_stderr(node_stderr,"subprocess forked") or check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(node_stderr,"IP Address 1") or check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True 

                        if "low_level_filter_130" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_130"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_130"] += 1

                elif check_error_in_stderr(node_stderr,"is not defined"):
                    if check_error_in_stderr(bun_stderr,"subprocess forked") or check_error_in_stderr(bun_stderr,"Response: ") or check_error_in_stderr(bun_stderr,"Server running at ") or check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                        move = True 

                        if "low_level_filter_130" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_130"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_130"] += 1

                if check_error_in_stderr(node_stderr,"Expected SameValue") and check_error_in_stderr(node_stderr,"to be true"):
                    if check_error_in_stderr(bun_stderr,"Current HOME Directory: ") or check_error_in_stderr(bun_stderr,"Response: ") or check_error_in_stderr(bun_stderr,"Server running at") or check_error_in_stderr(bun_stderr,"subprocess forked") or check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"IP Address 1") or check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True 

                        if "low_level_filter_130" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_130"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_130"] += 1
            
            
            #low level fitler 131
            if check_error_in_stderr(node_stderr,"is not defined"):
                if check_error_in_stderr(bun_stderr,"Can't find variable"):
                    if check_error_in_stderr(deno_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"should be configurable"):
                        move = True 

                elif check_error_in_stderr(deno_stderr,"The system cannot find the file specified"):
                    if check_error_in_stderr(bun_stderr,"no such file or directory"):
                        move = True 

                if move and "low_level_filter_131" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_131"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_131"] += 1

            #low level filter 132
            if check_error_in_stderr(node_stderr,"UnhandledPromiseRejection:"):
                if deno_stderr == bun_stderr:
                    move = True 

                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True 

                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True 

                elif check_error_in_stderr(deno_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True 

                elif check_error_in_stderr(deno_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz") and check_error_in_stderr(bun_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz"):
                    move = True 

                elif check_error_in_stderr(deno_stderr,"IP Address 1") and check_error_in_stderr(bun_stderr,"IP Address 1"):
                    move = True

                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True

                if move and "low_level_filter_132" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_132"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_132"] += 1

            

            #low level filter 133
            if check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property."):
                if node_stderr == deno_stderr:
                    move = True 
                elif check_error_in_stderr(node_stderr,"Response: "):
                    if check_error_in_stderr(deno_stderr,"Response: "):
                        move = True

                elif check_error_in_stderr(node_stderr,"Full Path: "):
                    if check_error_in_stderr(deno_stderr,"Full Path: "):
                        move = True

                elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                    if check_error_in_stderr(deno_stderr,"IP Address 1: "):
                        move = True

                elif check_error_in_stderr(node_stderr,"Server running at "):
                    if check_error_in_stderr(deno_stderr,"Server running at "):
                        move = True

                elif check_error_in_stderr(node_stderr,"RangeError: ") and check_error_in_stderr(node_stderr,"Invalid code point "):
                    if check_error_in_stderr(deno_stderr,"has already been declared"):
                        move = True 
                    elif check_error_in_stderr(deno_stderr,"TypeError: ") and check_error_in_stderr(deno_stderr,"Cannot set") and check_error_in_stderr(deno_stderr,"which has only a getter"):
                        move = True 
                    elif check_error_in_stderr(deno_stderr,"Uncaught (in promise)"):
                        move = True 

                elif check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"Expected SameValue") and check_error_in_stderr(node_stderr,"to be true"):
                    if check_error_in_stderr(deno_stderr,"TypeError: ") and check_error_in_stderr(deno_stderr,"Cannot create property"):
                        move = True 

                if move and "low_level_filter_133" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_133"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_133"] += 1  

            #low level filter 134
            if check_error_in_stderr(node_stderr,"Expected a Test262Error but got a ReferenceError"):
                if deno_stderr == bun_stderr:
                    move = True 

                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True 

                elif check_error_in_stderr(deno_stderr,"Server running at: ") and check_error_in_stderr(bun_stderr,"Server running at: "):
                    move = True

                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True

                elif check_error_in_stderr(deno_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True

                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True 

                if move and "low_level_filter_134" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_134"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_134"] += 1 

            
            #low level filter 135
            if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"message: ''"):
                if check_error_in_stderr(deno_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"message: \"\""):
                    if check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"IP Address 1"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True

                    if move and "low_level_filter_135" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_135"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_135"] += 1 

            #low level filter 136
            if check_error_in_stderr(deno_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"Test262Error"):
                msg = re.search(r'message: "(.*?)"', deno_stderr)
                if msg and msg.group(1) in bun_stderr:
                    if check_error_in_stderr(node_stderr,"has already been declared"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"IP Address 1"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Server running at "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"EADDRINUSE: address already in use"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"TypeError: Cannot convert"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"is not defined"):
                        move = True 

                    if move and "low_level_filter_136" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_136"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_136"] += 1

            #low level filter 137
            if check_error_in_stderr(deno_stderr,"ReferenceError: ") and check_error_in_stderr(deno_stderr,"is not defined"):
                if node_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(node_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True 
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"IP Address 1") and check_error_in_stderr(bun_stderr,"IP Address 1"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(bun_stderr,"ReferenceError: Can't find variable"):
                    if check_error_in_stderr(node_stderr,"EADDRINUSE"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"IP Address 1"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"SyntaxError: ") and check_error_in_stderr(node_stderr,"has already been declared"):
                        move = True 

                if move and "low_level_filter_137" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_137"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_137"] += 1

            #low level filter 138
            if check_error_in_stderr(node_stderr,"Expected a TypeError but got a Test262Error"):
                if deno_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1") and check_error_in_stderr(bun_stderr,"IP Address 1"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif deno_stderr == "//wsl.localhost/Ubuntu-24.04/root/node-deno-bun/fuzz/testFuzz\n\n" and bun_stderr == "\\\\wsl.localhost\\Ubuntu-24.04\\root\\node-deno-bun\\fuzz\\testFuzz\n\n":
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True 

                if move and "low_level_filter_138" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_138"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_138"] += 1 

            elif check_error_in_stderr(deno_stderr,"Expected a TypeError but got a Test262Error"):
                if node_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(node_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True 
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"IP Address 1") and check_error_in_stderr(bun_stderr,"IP Address 1"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(node_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True

                if move and "low_level_filter_138" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_138"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_138"] += 1
               
            #low level filter 139
            if check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                if check_error_in_stderr(deno_stderr,"d1c056a983786a38ca76a05cda240c7b86d77136"):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 

                        if "low_level_filter_139" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_139"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_139"] += 1

            #low level filter 140
            if check_error_in_stderr(node_stderr,"Expected a RangeError but got a TypeError"):
                if (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")):
                    if check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True 

                elif deno_stderr == bun_stderr:
                    move = True

                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True

                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True

                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True 

                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True  

                if move and "low_level_filter_140" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_140"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_140"] += 1


            #low level filter 141
            if check_error_in_stderr(node_stderr,"ReferenceError: ") and check_error_in_stderr(node_stderr,"is not defined"):
                if check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared"):
                    if check_error_in_stderr(bun_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"that shadows a"):
                        move = True 

                        if move and "low_level_filter_141" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_141"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_141"] += 1

            #low level filter 142
            if check_error_in_stderr(deno_stderr,"TypeError: ") and check_error_in_stderr(deno_stderr,"is not a function"):
                if check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True
                elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True 
                elif node_stderr == bun_stderr:
                    move = True

                if move and "low_level_filter_142" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_142"] = 1
                else:
                    if move: 
                        low_level_filter_counts["low_level_filter_142"] += 1


            #low level fitler 143
            if check_error_in_stderr(node_stderr,"Full Path: "):
                if check_error_in_stderr(deno_stderr,"Full Path: "):
                    if check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True 

                        if move and "low_level_filter_143" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_143"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_143"] += 1

            #low level filter 144
            if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"should have an own property"):
                if check_error_in_stderr(deno_stderr,"Uncaught (in promise) ") or check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                    if check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                        move = True 

                        if move and "low_level_filter_144" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_144"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_144"] += 1

                elif check_error_in_stderr(deno_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"should have an own property"):
                    if check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                        move = True 

                        if move and "low_level_filter_144" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_144"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_144"] += 1


            elif check_error_in_stderr(deno_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"should have an own property"):
                if node_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True
                elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"IP Address 1") and check_error_in_stderr(bun_stderr,"IP Address 1"):
                    move = True
                elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True
                elif check_error_in_stderr(node_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True

                if move and "low_level_filter_144" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_144"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_144"] += 1


            #low level filter 145
            if check_error_in_stderr(deno_stderr,"which has only a getter") or (check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared")):
                if check_error_in_stderr(bun_stderr,"Attempted to assign to readonly property"):
                    if check_error_in_stderr(node_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Current HOME Directory"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True  
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"should match"):
                        move = True 

                elif check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"which has only a getter"):
                    if check_error_in_stderr(bun_stderr,"EADDRINUSE"):
                        move = True 

                    if move and "low_level_filter_145" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_145"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_145"] += 1
                    
            #low level filter 146
            if check_error_in_stderr(node_stderr,"Cannot define property") and check_error_in_stderr(node_stderr,"is not extensible"):
                if check_error_in_stderr(bun_stderr,"Attempting to define property on object that is not extensible"):
                    if check_error_in_stderr(deno_stderr,"Uncaught (in promise)"):
                        move = True 

                        if move and "low_level_filter_146" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_146"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_146"] += 1

            #low level filter 147
            if check_error_in_stderr(node_stderr,"TypeError") and check_error_in_stderr(node_stderr,"must be of type function"):

                if deno_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(deno_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True

                if move and "low_level_filter_147" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_147"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_147"] += 1

            #low level filter 148
            if check_error_in_stderr(node_stderr,"Error: Exception occurred in ") : 
                if check_error_in_stderr(deno_stderr,"Error: Exception occurred in "):
                    if check_error_in_stderr(bun_stderr,"error: Exception occurred in "):
                        move = True 

                        if move and "low_level_filter_148" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_148"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_148"] += 1

            #low level filter 149
            if check_error_in_stderr(deno_stderr,"cannot find the file specified. (os error ") or check_error_in_stderr(deno_stderr,"No such file or directory (os error "):
                if check_error_in_stderr(bun_stderr,"operation not permitted") or check_error_in_stderr(bun_stderr,"No such file or directory"):
                    if check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"/home/abdullah/node-deno-bun/fuzz/testFuzz\n\n"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True

                    if move and "low_level_filter_149" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_149"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_149"] += 1

            #low level filter 150
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"called on null or undefined"):
                if check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"): 
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True 
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif deno_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                    if check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True

                if move and "low_level_filter_150" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_150"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_150"] += 1

            #low level filter 151
            if check_error_in_stderr(bun_stderr,"Expected a RangeError but got a ReferenceError"):
                if deno_stderr == node_stderr:
                    move = True 
                if check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(node_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(node_stderr,"subprocess forked"): 
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(node_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(node_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(node_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                    move = True 
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(node_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
        

                if move and "low_level_filter_151" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_151"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_151"] += 1

            #low level filter 152
            if check_error_in_stderr(node_stderr,"undefined"):
                if deno_stderr == bun_stderr:
                    move = True 
                if check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"): 
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True 
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
        

                if move and "low_level_filter_152" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_152"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_152"] += 1

            #low level filter 153
            if check_error_in_stderr(bun_stderr,"Expected a ReferenceError but got a TypeError"):
                if deno_stderr == node_stderr:
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(node_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(node_stderr,"subprocess forked"): 
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(node_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(node_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(node_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                    move = True 
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(node_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True 
        

                if move and "low_level_filter_153" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_153"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_153"] += 1

            elif check_error_in_stderr(deno_stderr,"Expected a ReferenceError but got a TypeError"):
                if bun_stderr == node_stderr:
                    move = True 
                elif check_error_in_stderr(bun_stderr,"Server running at") and check_error_in_stderr(node_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(bun_stderr,"subprocess forked") and check_error_in_stderr(node_stderr,"subprocess forked"): 
                    move = True
                elif check_error_in_stderr(bun_stderr,"Response: ") and check_error_in_stderr(node_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(bun_stderr,"Full Path: ") and check_error_in_stderr(node_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(bun_stderr,"IP Address 1: ") and check_error_in_stderr(node_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(bun_stderr,"Current HOME Directory: ") and check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                    move = True 
                elif (check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(node_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True 
        

                if move and "low_level_filter_153" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_153"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_153"] += 1
            

            #low level filter 154
            if check_error_in_stderr(bun_stderr,"Expected a RangeError but got a ReferenceError"):
                if check_error_in_stderr(deno_stderr,"Expected a RangeError but got a ReferenceError"):
                    if check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True 

                        if move and "low_level_filter_154" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_154"] = 1
                        else:
                            low_level_filter_counts["low_level_filter_154"] += 1

            #low level filter 155
            if check_error_in_stderr(node_stderr,"Assertion failed: "):
                if deno_stderr == bun_stderr:
                    move = True 
                if check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"): 
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True 
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True 

                if move and "low_level_filter_155" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_155"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_155"] += 1

            
            #low level filter 156
            if check_error_in_stderr(node_stderr,"TypeError: Invalid property descriptor"):
                if deno_stderr == bun_stderr:
                    move = True 
                if check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"): 
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(bun_stderr,"Current HOME Directory: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True 
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(bun_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True 

                if move and "low_level_filter_156" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_156"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_156"] += 1

            #low level filter 157
            if check_error_in_stderr(node_stderr,"TypeError: ") and check_error_in_stderr(node_stderr,"Cannot both specify accessors"):
                if check_error_in_stderr(deno_stderr,"TypeError: ") and check_error_in_stderr(deno_stderr,"Cannot both specify accessors"):
                    if check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"Expected a ") and check_error_in_stderr(bun_stderr,"but no exception was thrown at all"):
                        move = True 

                        if move and "low_level_filter_157" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_157"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_157"] += 1

            #low level filter 158
            if check_error_in_stderr(node_stderr,"SerrooSer"):
                if check_error_in_stderr(deno_stderr,"Server running at "):
                    if check_error_in_stderr(bun_stderr,"Server running at "):
                        move = True 

                        if move and "low_level_filter_158" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_158"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_158"] += 1


            #low level filter 159
            if check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(bun_stderr,"Expected SameValue") and check_error_in_stderr(bun_stderr,"to be true"):
                if deno_stderr == node_stderr:
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(node_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(node_stderr,"subprocess forked"): 
                    move = True
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(node_stderr,"Response: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(node_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(node_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory: ") and check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                    move = True 
                elif (check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") or check_error_in_stderr(node_stderr,"da39a3ee5e6b4b0d3255bfef95601890afd80709")) and check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                    if check_error_in_stderr(node_stderr,"Current HOME Directory: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"Expected SameValue") and check_error_in_stderr(node_stderr,"to be true"):
                        move = True 

        
                if move and "low_level_filter_159" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_159"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_159"] += 1
                    
            #low level filter 160
            if check_error_in_stderr(bun_stderr,"TypeError: ") and check_error_in_stderr(bun_stderr,"Attempting to") and check_error_in_stderr(bun_stderr,"of an unconfigurable property"):
                if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"Test262Error"):
                    move = True 

                    if move and "low_level_filter_160" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_160"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_160"] += 1

            #low level filter 161
            if check_error_in_stderr(node_stderr,"function(){return 1} >= function(){return 1"):
                if check_error_in_stderr(deno_stderr,"function(){return 1} >= function(){return 1"):
                    if check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"subprocess forked"):
                        move = True 
                    elif check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(bun_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"Expected SameValue") and check_error_in_stderr(node_stderr,"to be true"):
                        move = True
                    
                    if move and "low_level_filter_161" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_161"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_161"] += 1

            #low level filter 162
            if check_error_in_stderr(deno_stderr,"Uncaught (in promise) "):
                if check_error_in_stderr(bun_stderr,"no such file or directory"):
                    if check_error_in_stderr(node_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"Expected SameValue") and check_error_in_stderr(node_stderr,"to be true"):
                        move = True 

                    if move and "low_level_filter_162" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_162"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_162"] += 1

            #low level filter 163
            if check_error_in_stderr(node_stderr,"function(){return 1}.toString()"):
                if check_error_in_stderr(bun_stderr,"function(){return 1}.toString()"):
                    if check_error_in_stderr(deno_stderr,"There is not enough space on the disk. (os error "):
                        move = True 
                    elif check_error_in_stderr(deno_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"Response: "):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"subprocess forked"):
                        move = True 
                    elif check_error_in_stderr(deno_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"Test262Error") and check_error_in_stderr(node_stderr,"Expected SameValue") and check_error_in_stderr(node_stderr,"to be true"):
                        move = True 

                    if move and "low_level_filter_163" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_163"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_163"] += 1

            #low level filter 164
            if deno_stderr == "" or deno_stderr is None:
                if check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True 
                elif check_error_in_stderr(node_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True 
                elif check_error_in_stderr(node_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(node_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True

                if move and "low_level_filter_164" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_164"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_164"] += 1

            #low level filter 165
            if node_stderr == "":
                if deno_stderr == "":
                    if check_error_in_stderr(bun_stderr,"Response: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True

                    if move and "low_level_filter_165" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_165"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_165"] += 1

            #low level filter 166
            if node_stderr == "":
                if bun_stderr == "":
                    if check_error_in_stderr(deno_stderr,"Response: "):
                        move = True 
                    elif check_error_in_stderr(deno_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(deno_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True

                    if move and "low_level_filter_166" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_166"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_166"] += 1

            #low level filter 167
            if deno_stderr == "":
                if bun_stderr == "":
                    if check_error_in_stderr(node_stderr,"Response: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True

                    if move and "low_level_filter_167" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_167"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_167"] += 1


            #low level filter 168
            if check_error_in_stderr(deno_stderr,"SyntaxError: ") and check_error_in_stderr(deno_stderr,"has already been declared"):
                if check_error_in_stderr(bun_stderr,"SyntaxError: ") and check_error_in_stderr(bun_stderr,"that shadows a "):
                    if check_error_in_stderr(node_stderr,"Response: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True

                    if move and "low_level_filter_168" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_168"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_168"] += 1
                elif check_error_in_stderr(bun_stderr,"operation not permitted"):
                    if check_error_in_stderr(node_stderr,"Response: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True

                    if move and "low_level_filter_168" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_168"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_168"] += 1

            #low level filter 169
            if check_error_in_stderr(deno_stderr,"AddrInUse: "):
                if check_error_in_stderr(bun_stderr,"EADDRINUSE"):
                    if check_error_in_stderr(node_stderr,"Response: "):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"Current HOME Directory"):
                        move = True 
                    elif check_error_in_stderr(node_stderr,"subprocess forked"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Server running at"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                        move = True
                    elif check_error_in_stderr(node_stderr,"IP Address 1: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"Full Path: "):
                        move = True
                    elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                        move = True

                    if move and "low_level_filter_169" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_169"] = 1
                    else:
                        if move:
                            low_level_filter_counts["low_level_filter_169"] += 1

            #low level filter 170
            if check_error_in_stderr(deno_stderr,"Expected a Test262Error but got a ReferenceError"):
                if node_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(node_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True 
                elif check_error_in_stderr(node_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True 
                elif check_error_in_stderr(node_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(node_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(node_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True

                if move and "low_level_filter_170" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_170"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_170"] += 1

            #low level filter 171
            if check_error_in_stderr(node_stderr,"ERR_UNESCAPED_CHARACTERS"):
                if deno_stderr == bun_stderr:
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(bun_stderr,"Response: "):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory") and check_error_in_stderr(bun_stderr,"Current HOME Directory"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(bun_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(bun_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(bun_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(bun_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(bun_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(bun_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True

                if move and "low_level_filter_171" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_171"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_171"] += 1

            #low level filter 172
            if check_error_in_stderr(bun_stderr,"Expected identifier but found "):
                if deno_stderr == node_stderr:
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Response: ") and check_error_in_stderr(node_stderr,"Response: "):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"Current HOME Directory") and check_error_in_stderr(node_stderr,"Current HOME Directory"):
                    move = True 
                elif check_error_in_stderr(deno_stderr,"subprocess forked") and check_error_in_stderr(node_stderr,"subprocess forked"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Server running at") and check_error_in_stderr(node_stderr,"Server running at"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3") and check_error_in_stderr(node_stderr,"a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"):
                    move = True
                elif check_error_in_stderr(deno_stderr,"IP Address 1: ") and check_error_in_stderr(node_stderr,"IP Address 1: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"Full Path: ") and check_error_in_stderr(node_stderr,"Full Path: "):
                    move = True
                elif check_error_in_stderr(deno_stderr,"root:x:0:0:root:/root:/bin") and check_error_in_stderr(node_stderr,"root:x:0:0:root:/root:/bin"):
                    move = True

                if move and "low_level_filter_172" not in low_level_filter_counts:
                    low_level_filter_counts["low_level_filter_172"] = 1
                else:
                    if move:
                        low_level_filter_counts["low_level_filter_172"] += 1


            #low level filter 173
            if check_error_in_stderr(node_stderr,"Step 5 occurred out of order"):
                if check_error_in_stderr(deno_stderr,"Step 5 occurred out of order"):
                    if check_error_in_stderr(bun_stderr,"Step 5 occurred out of order"):
                        move = True 

                        if move and "low_level_filter_173" not in low_level_filter_counts:
                            low_level_filter_counts["low_level_filter_173"] = 1
                        else:
                            if move:
                                low_level_filter_counts["low_level_filter_173"] += 1

            '''#low level filter 174
            if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"Test262Error"):
                #cleaned_message_bun = re.sub(r'\\(.)', r'\1', bun_stderr)
                #cleaned_message_deno = re.sub(r'\\(.)', r'\1', bun)
                msg = re.search(r'(#\d+\.\d+: ".*?")', node_stderr)

                if msg and msg.group(1) in deno_stderr:
                    move = True 

                    if move and "low_level_filter_174" not in low_level_filter_counts:
                        low_level_filter_counts["low_level_filter_174"] = 1
                    else:
                        low_level_filter_counts["low_level_filter_174"] += 1'''


            #dynamic filter
            if error_similarity(node_preprocessed,bun_preprocessed) >= 90:
                if check_error_in_stderr(deno_stderr,"has already been declared"):
                    move = True

                    if "dynamic_filter" not in low_level_filter_counts:
                        low_level_filter_counts["dynamic_filter"] = 1
                    else:
                        low_level_filter_counts["dynamic_filter"] += 1

                elif error_similarity(deno_preprocessed,bun_preprocessed) >=92:
                    if error_similarity(node_preprocessed,deno_preprocessed)>=90:
                        move = True

                        if "dynamic_filter" not in low_level_filter_counts:
                            low_level_filter_counts["dynamic_filter"] = 1
                        else:
                            low_level_filter_counts["dynamic_filter"] += 1

            if move == True:
                #move_file(file_path,filename,destination_folder)
                filter_logs[key] = log 
            else:
                remaining_logs[key] = log 


    dest = os.path.join(cwd, f'{round}_filtered_op.json')
    rem = os.path.join(cwd,f'{round}_remaining.json')

    

    with open(dest, 'w') as dest_file:
        json.dump(filter_logs, dest_file, indent=4)

    with open(rem, 'w') as dest_file:
        json.dump(remaining_logs, dest_file, indent=4)

    shutil.move(dest, os.path.join(filtered, os.path.basename(dest)))
    shutil.move(rem, os.path.join(filtered, os.path.basename(rem)))

    filter_logs = {}
    remaining_logs = {} 

    freq_folder = os.path.join(cwd,"filtered","frequency")
    os.makedirs(freq_folder, exist_ok=True)

    low_filt_dest = os.path.join(freq_folder,f"{round}_low_level_filter_count.json")
    filt_dest = os.path.join(freq_folder,f"{round}_filter_count.json")

    print(low_level_filter_counts)
    print("\n")
    print(filter_counts)

    with open(low_filt_dest, "w") as file:
        json.dump(low_level_filter_counts, file, indent=4)

    with open(filt_dest, "w") as file:
        json.dump(filter_counts, file, indent=4) 

    filter_counts = {}
    low_level_filter_counts = {}

    
print("Filter Done...")

########################################### END OF FILTER ###########################################################################


#pattern1 = r"\S*\.js\S*"
#pattern2 = r'\x1b|\bfile://'



cluster_source_folder = os.path.join(cwd,'filtered')
cluster_folder = os.path.join(cwd,'cluster')

if not os.path.exists(cluster_folder):
    os.makedirs(cluster_folder)

#node_only_cluster = get_cluster_files(node_only_destination_directory)
node_only_cluster = {}
deno_only_cluster = {}
bun_only_cluster = {}

node_deno_cluster = {}
deno_bun_cluster = {}
node_bun_cluster = {}

node_deno_bun = {}


def extract_error_string(stderr):
    start_token = 'error:'
    if stderr!=None:
        start_idx = stderr.find(start_token)
        if start_idx != -1:
            start_idx += len(start_token)
            end_idx = stderr.find('\n', start_idx)
            if end_idx != -1:
                return stderr[start_idx:end_idx].strip()
        return None
    else:
         return None 

def check_error_in_stderr(stderr, error_str):
    if stderr != None and error_str!=None:         
        return error_str.lower() in stderr.lower()
    else:
         return False 




# Function to add a new list with a unique key
def add_new_file(dict,key,item):
    if key not in dict:  
        #node_only_list[key] = []
        print("No such cluster")
        #node_only_list[key].append(item)
    else:
        #print(f"{key} already exists!")
        dict[key].append(item)

def add_new_cluster(clusters):
    # Extract cluster numbers from existing keys

    #for name in clusters:
     #   if 

    cluster_numbers = [
        int(name.split('_')[1]) for name in clusters if name.startswith("cluster_")
    ]
    
    # Find the highest cluster number
    max_number = max(cluster_numbers, default=0)
    
    # Create the new cluster name with incremented number
    new_cluster_name = f"cluster_{max_number + 1}"
    
    # Add the new cluster to the dictionary with an empty list (or any other default value)
    clusters[new_cluster_name] = []
    
    return new_cluster_name  # Optionally return the new cluster name

    
#for dirpath, dirnames, filenames in os.walk(round_folder):
pattern = r"round_(\d+)_remaining.json"

for source_filename in os.listdir(cluster_source_folder):    
            
    round_no = "0"        
    if source_filename.endswith('.json'):
        #print(source_filename)
        if "remaining" in source_filename:
            match = re.search(pattern, source_filename)
            if match:
                round_no = match.group(1)
                round_path = os.path.join(cluster_folder,"round_" + round_no)
            
                '''if not os.path.exists(round_path):
                    os.makedirs(round_path)'''

            source_file_path = os.path.join(cluster_source_folder,source_filename)

            # Read the JSON file
            with open(source_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            for key,logs in data.items():
                    
                node_stderr = logs["node"]
                deno_stderr = logs["deno"]
                bun_stderr = logs["bun"]
        
                if node_stderr != None and node_stderr!="":
                    node_stderr = preprocess_error(node_stderr)
                    node_stderr = extract_meaningful_error_message_node(node_stderr)
                if deno_stderr!=None and deno_stderr!="":
                    deno_stderr = preprocess_error(deno_stderr)
                    deno_stderr = extract_meaningful_error_message_deno(deno_stderr)
                if bun_stderr!="" and bun_stderr!=None:
                    bun_stderr = preprocess_error(bun_stderr)
                    bun_stderr = extract_meaningful_error_message_node(bun_stderr)
                    bun_stderr = re.sub(r"[^\x00-\x7F]+", "",bun_stderr)

                if (node_stderr!="" and node_stderr!=None) and (deno_stderr=="" or deno_stderr==None) and (bun_stderr == "" or bun_stderr==None):

                    flag = 0
                
                    if not node_only_cluster:
                        print("reached here")
                        cname = add_new_cluster(node_only_cluster)
                        add_new_file(node_only_cluster,cname,key)
                        continue
                
                    for cluster_name, lst in node_only_cluster.items():
                        
                        for item in lst:
                        
                            list_path = os.path.join(cluster_source_folder,"round_"+round_no+"_remaining.json")
                            with open(list_path, 'r', encoding='utf-8') as f:
                                fdata = json.load(f)

                            #error_string = fdata[0].get('node', '')
                            filename = fdata[item]
                            error_string = filename['node']

                            error_string = preprocess_error(error_string)
                            error_string = extract_meaningful_error_message_node(error_string)

                            similarity_percentage = error_similarity(node_stderr, error_string)

                            if similarity_percentage >= 90:
                                flag = 1
                                print("Node similarity")
                                node_only_cluster[cluster_name].append(key)
                                break
                            break
                    
                        if flag == 1:
                            break 
                
                    if flag == 1:
                        flag = 0
                    else:
                        print("no condition satisfied")
                        cname = add_new_cluster(node_only_cluster)
                        add_new_file(node_only_cluster,cname,key)
                        continue
                    
                if (node_stderr=="" or node_stderr==None) and (deno_stderr!="" and deno_stderr!=None) and (bun_stderr=="" or bun_stderr==None):

                    flag = 0
                
                    if not deno_only_cluster:
                        print("reached here")
                        cname = add_new_cluster(deno_only_cluster)
                        add_new_file(deno_only_cluster,cname,key)
                        continue
                
                    for cluster_name, lst in deno_only_cluster.items():
                    
                        #print(cluster_name)
                        for item in lst:
                        
                            #print(item)
                            list_path = os.path.join(cluster_source_folder,"round_"+round_no+"_remaining.json")
                            #print(list_path)
                            with open(list_path, 'r', encoding='utf-8') as f:
                                fdata = json.load(f)
                        
                            #error_string = fdata[0].get('deno', '')
                            filename = fdata[item]
                            error_string = filename['deno']

                            error_string = preprocess_error(error_string)
                            error_string = extract_meaningful_error_message_deno(error_string)

                            similarity_percentage = error_similarity(deno_stderr, error_string)

                            if similarity_percentage >= 92:
                                flag = 1
                                deno_only_cluster[cluster_name].append(key)
                                print("Deno similarity")
                                #print(deno_stderr," ",error_string," ",similarity_percentage," ",source_filename," ",item,"\n")
                                break
                            break

                        if flag == 1:
                            break 
                
                    if flag == 1:
                        flag = 0
                    else:
                        print("no condition satisfied")
                        cname = add_new_cluster(deno_only_cluster)
                        add_new_file(deno_only_cluster,cname,key)
                        continue

                if (node_stderr=="" or node_stderr==None) and (deno_stderr=="" or deno_stderr==None) and (bun_stderr!="" and bun_stderr!=None):

                    flag = 0
                
                    if not bun_only_cluster:
                        print("reached here")
                        cname = add_new_cluster(bun_only_cluster)
                        add_new_file(bun_only_cluster,cname,key)
                        continue
                
                    for cluster_name, lst in bun_only_cluster.items():
                        #print(cluster_name," : ",lst)
                        for item in lst:
                        
                            #print(item)
                            list_path = os.path.join(cluster_source_folder,"round_"+round_no+"_remaining.json")
                            #print(list_path)
                            #print(source_file_path)
                            with open(list_path, 'r', encoding='utf-8') as f:
                                fdata = json.load(f)
                                #print(fdata)
                                '''if item in fdata.items():
                                    print(True)
                                else:
                                    print(False)'''
                        
                            #error_string = fdata[0].get('bun', '')
                            filename = fdata[item]
                            error_string = filename['bun']

                            error_string = preprocess_error(error_string)
                            error_string = extract_meaningful_error_message_node(error_string)
                            error_string = re.sub(r"[^\x00-\x7F]+", "",error_string)

                            similarity_percentage = error_similarity(bun_stderr, error_string)

                            if similarity_percentage >= 90:
                                flag = 1
                                print("Bun similarity")
                                bun_only_cluster[cluster_name].append(key)
                                break
                            break

                        if flag == 1:
                            break 
                
                    if flag == 1:
                        flag = 0
                    else:
                        print("no condition satisfied")
                        cname = add_new_cluster(bun_only_cluster)
                        add_new_file(bun_only_cluster,cname,key)
                        continue

                if (node_stderr!="" and node_stderr!=None) and (deno_stderr!="" and deno_stderr!=None) and (bun_stderr == "" or bun_stderr==None):

                    flag = 0
                
                    if not node_deno_cluster:
                        print("reached here")
                        cname = add_new_cluster(node_deno_cluster)
                        add_new_file(node_deno_cluster,cname,key)
                        continue
                
                    for cluster_name, lst in node_deno_cluster.items():
                        
                        for item in lst:
                        
                            list_path = os.path.join(cluster_source_folder,"round_"+round_no+"_remaining.json")
                            with open(list_path, 'r', encoding='utf-8') as f:
                                fdata = json.load(f)

                            #error_string = fdata[0].get('node', '')
                            filename = fdata[item]
                            error_string_node = filename['node']
                            error_string_deno = filename['deno']

                            error_string_node = preprocess_error(error_string_node)
                            error_string_node = extract_meaningful_error_message_node(error_string_node)

                            error_string_deno = preprocess_error(error_string_deno)
                            error_string_deno = extract_meaningful_error_message_node(error_string_deno)

                            similarity_percentage_node = error_similarity(node_stderr, error_string_node)
                            similarity_percentage_deno = error_similarity(deno_stderr, error_string_deno)

                            if similarity_percentage_node >= 90 and similarity_percentage_deno >= 92:
                                flag = 1
                                print("Node-Deno similarity")
                                node_deno_cluster[cluster_name].append(key)
                                break
                            break
                    
                        if flag == 1:
                            break 
                
                    if flag == 1:
                        flag = 0
                    else:
                        print("no condition satisfied")
                        cname = add_new_cluster(node_deno_cluster)
                        add_new_file(node_deno_cluster,cname,key)
                        continue
                    
                if (node_stderr=="" or node_stderr==None) and (deno_stderr!="" and deno_stderr!=None) and (bun_stderr!="" and bun_stderr!=None):

                    flag = 0
                
                    if not deno_bun_cluster:
                        print("reached here")
                        cname = add_new_cluster(deno_bun_cluster)
                        add_new_file(deno_bun_cluster,cname,key)
                        continue
                
                    for cluster_name, lst in deno_bun_cluster.items():
                    
                        #print(cluster_name)
                        for item in lst:
                        
                            #print(item)
                            list_path = os.path.join(cluster_source_folder,"round_"+round_no+"_remaining.json")
                            #print(list_path)
                            with open(list_path, 'r', encoding='utf-8') as f:
                                fdata = json.load(f)
                        
                            #error_string = fdata[0].get('deno', '')
                            filename = fdata[item]
                            error_string_deno = filename['deno']
                            error_string_bun = filename['bun']

                            error_string_deno = preprocess_error(error_string_deno)
                            error_string_deno = extract_meaningful_error_message_deno(error_string_deno)

                            error_string_bun = preprocess_error(error_string_bun)
                            error_string_bun = extract_meaningful_error_message_node(error_string_bun)
                            error_string_bun = re.sub(r"[^\x00-\x7F]+", "",error_string_bun)


                            similarity_percentage_deno = error_similarity(deno_stderr, error_string_deno)
                            similarity_percentage_bun = error_similarity(bun_stderr, error_string_bun)

                            if similarity_percentage_deno >= 92 and similarity_percentage_bun >= 90:
                                flag = 1
                                deno_bun_cluster[cluster_name].append(key)
                                print("Deno-Bun similarity")
                                #print(deno_stderr," ",error_string," ",similarity_percentage," ",source_filename," ",item,"\n")
                                break
                            break

                        if flag == 1:
                            break 
                
                    if flag == 1:
                        flag = 0
                    else:
                        print("no condition satisfied")
                        cname = add_new_cluster(deno_bun_cluster)
                        add_new_file(deno_bun_cluster,cname,key)
                        continue

                if (node_stderr!="" and node_stderr!=None) and (deno_stderr=="" or deno_stderr==None) and (bun_stderr!="" and bun_stderr!=None):

                    flag = 0
                
                    if not node_bun_cluster:
                        print("reached here")
                        cname = add_new_cluster(node_bun_cluster)
                        add_new_file(node_bun_cluster,cname,key)
                        continue
                
                    for cluster_name, lst in node_bun_cluster.items():
                        #print(cluster_name," : ",lst)
                        for item in lst:
                        
                            #print(item)
                            list_path = os.path.join(cluster_source_folder,"round_"+round_no+"_remaining.json")
                            #print(list_path)
                            #print(source_file_path)
                            with open(list_path, 'r', encoding='utf-8') as f:
                                fdata = json.load(f)
                                #print(fdata)
                                '''if item in fdata.items():
                                    print(True)
                                else:
                                    print(False)'''
                        
                            #error_string = fdata[0].get('bun', '')
                            filename = fdata[item]
                            error_string_bun = filename['bun']
                            error_string_node = filename['node']

                            error_string_bun = preprocess_error(error_string_bun)
                            error_string_bun = extract_meaningful_error_message_node(error_string_bun)
                            error_string_bun = re.sub(r"[^\x00-\x7F]+", "",error_string_bun)

                            error_string_node = preprocess_error(error_string_node)
                            error_string_node = extract_meaningful_error_message_node(error_string_node)

                            similarity_percentage_bun = error_similarity(bun_stderr, error_string_bun)
                            similarity_percentage_node = error_similarity(node_stderr,error_string_node)

                            if similarity_percentage_bun >= 90 and similarity_percentage_node >= 90:
                                flag = 1
                                print("Node-Bun similarity")
                                node_bun_cluster[cluster_name].append(key)
                                break
                            break

                        if flag == 1:
                            break 
                
                    if flag == 1:
                        flag = 0
                    else:
                        print("no condition satisfied")
                        cname = add_new_cluster(node_bun_cluster)
                        add_new_file(node_bun_cluster,cname,key)
                        continue

                if (node_stderr!="" and node_stderr!=None) and (deno_stderr!="" and deno_stderr!=None) and (bun_stderr != "" and bun_stderr!=None):

                    flag = 0
                
                    if not node_deno_bun:
                        print("reached here")
                        cname = add_new_cluster(node_deno_bun)
                        add_new_file(node_deno_bun,cname,key)
                        continue
                
                    for cluster_name, lst in node_deno_bun.items():
                        
                        for item in lst:
                        
                            list_path = os.path.join(cluster_source_folder,"round_"+round_no+"_remaining.json")
                            with open(list_path, 'r', encoding='utf-8') as f:
                                fdata = json.load(f)

                            #error_string = fdata[0].get('node', '')
                            filename = fdata[item]
                            error_string_node = filename['node']
                            error_string_deno = filename['deno']
                            error_string_bun = filename['bun']

                            error_string_node = preprocess_error(error_string_node)
                            error_string_node = extract_meaningful_error_message_node(error_string_node)

                            error_string_deno = preprocess_error(error_string_deno)
                            error_string_deno = extract_meaningful_error_message_deno(error_string_deno)

                            error_string_bun = preprocess_error(error_string_bun)
                            error_string_bun = extract_meaningful_error_message_node(error_string_bun)
                            error_string_bun = re.sub(r"[^\x00-\x7F]+", "",error_string_bun)

                            similarity_percentage_node = error_similarity(node_stderr, error_string_node)
                            similarity_percentage_deno = error_similarity(deno_stderr, error_string_deno)
                            similarity_percentage_bun = error_similarity(bun_stderr, error_string_bun)

                            if similarity_percentage_node >= 90 and similarity_percentage_deno >= 92 and similarity_percentage_bun >= 90:
                                flag = 1
                                print("Node-Deno-Bun similarity")
                                node_deno_bun[cluster_name].append(key)
                                break
                            break
                    
                        if flag == 1:
                            break 
                
                    if flag == 1:
                        flag = 0
                    else:
                        print("no condition satisfied")
                        cname = add_new_cluster(node_deno_bun)
                        add_new_file(node_deno_bun,cname,key)
                        continue
            
            if round_no != "0":
                source_directory = os.path.join(cluster_source_folder,source_filename)

                destination_directory1 = os.path.join(cwd,"cluster","node_only","round_"+round_no)
                destination_directory2 = os.path.join(cwd,"cluster","deno_only","round_"+round_no)
                destination_directory3 = os.path.join(cwd,"cluster","bun_only","round_"+round_no) 

                destination_directory4 = os.path.join(cwd,"cluster","node_deno","round_"+round_no)
                destination_directory5 = os.path.join(cwd,"cluster","deno_bun","round_"+round_no)
                destination_directory6 = os.path.join(cwd,"cluster","node_bun","round_"+round_no)

                destination_directory7 = os.path.join(cwd,"cluster","node_deno_bun","round_"+round_no)

                if not os.path.exists(destination_directory1):
                    os.makedirs(destination_directory1)
                if not os.path.exists(destination_directory2):
                    os.makedirs(destination_directory2)
                if not os.path.exists(destination_directory3):
                    os.makedirs(destination_directory3)


                if not os.path.exists(destination_directory4):
                    os.makedirs(destination_directory4)
                if not os.path.exists(destination_directory5):
                    os.makedirs(destination_directory5)
                if not os.path.exists(destination_directory6):
                    os.makedirs(destination_directory6)

                if not os.path.exists(destination_directory7):
                    os.makedirs(destination_directory7)
                

                with open(source_directory, 'r', encoding='utf-8') as file:
                    data_file = json.load(file) 

                for cluster_name, file_list in node_only_cluster.items():
                    cluster_data = {}
    
                    # Collect relevant data for the current cluster
                    for file_key in file_list:
                        if file_key in data_file:  # Ensure the key exists in the source data
                            cluster_data[file_key] = data_file[file_key]
                        else:
                            print(f"Warning: {file_key} not found in source file.")

                    # Write the cluster data to a new JSON file
                    cluster_file_path = os.path.join(destination_directory1, f"{cluster_name}.json")
                    with open(cluster_file_path, 'w', encoding='utf-8') as cluster_file:
                        json.dump(cluster_data, cluster_file, indent=4, ensure_ascii=False)
                    print(f"Cluster {cluster_name} data written to {cluster_file_path}")

                for cluster_name, file_list in deno_only_cluster.items():
                    cluster_data = {}
    
                    # Collect relevant data for the current cluster
                    for file_key in file_list:
                        if file_key in data_file:  # Ensure the key exists in the source data
                            cluster_data[file_key] = data_file[file_key]
                        else:
                            print(f"Warning: {file_key} not found in source file.")

                    # Write the cluster data to a new JSON file
                    cluster_file_path = os.path.join(destination_directory2, f"{cluster_name}.json")
                    with open(cluster_file_path, 'w', encoding='utf-8') as cluster_file:
                        json.dump(cluster_data, cluster_file, indent=4, ensure_ascii=False)
                    print(f"Cluster {cluster_name} data written to {cluster_file_path}")

                for cluster_name, file_list in bun_only_cluster.items():
                    cluster_data = {}
    
                    # Collect relevant data for the current cluster
                    for file_key in file_list:
                        if file_key in data_file:  # Ensure the key exists in the source data
                            cluster_data[file_key] = data_file[file_key]
                        else:
                            print(f"Warning: {file_key} not found in source file.")

                    # Write the cluster data to a new JSON file
                    cluster_file_path = os.path.join(destination_directory3, f"{cluster_name}.json")
                    with open(cluster_file_path, 'w', encoding='utf-8') as cluster_file:
                        json.dump(cluster_data, cluster_file, indent=4, ensure_ascii=False)
                    print(f"Cluster {cluster_name} data written to {cluster_file_path}")

                for cluster_name, file_list in node_deno_cluster.items():
                    cluster_data = {}
    
                    # Collect relevant data for the current cluster
                    for file_key in file_list:
                        if file_key in data_file:  # Ensure the key exists in the source data
                            cluster_data[file_key] = data_file[file_key]
                        else:
                            print(f"Warning: {file_key} not found in source file.")

                    # Write the cluster data to a new JSON file
                    cluster_file_path = os.path.join(destination_directory4, f"{cluster_name}.json")
                    with open(cluster_file_path, 'w', encoding='utf-8') as cluster_file:
                        json.dump(cluster_data, cluster_file, indent=4, ensure_ascii=False)
                    print(f"Cluster {cluster_name} data written to {cluster_file_path}")

                for cluster_name, file_list in deno_bun_cluster.items():
                    cluster_data = {}
    
                    # Collect relevant data for the current cluster
                    for file_key in file_list:
                        if file_key in data_file:  # Ensure the key exists in the source data
                            cluster_data[file_key] = data_file[file_key]
                        else:
                            print(f"Warning: {file_key} not found in source file.")

                    # Write the cluster data to a new JSON file
                    cluster_file_path = os.path.join(destination_directory5, f"{cluster_name}.json")
                    with open(cluster_file_path, 'w', encoding='utf-8') as cluster_file:
                        json.dump(cluster_data, cluster_file, indent=4, ensure_ascii=False)
                    print(f"Cluster {cluster_name} data written to {cluster_file_path}")

                for cluster_name, file_list in node_bun_cluster.items():
                    cluster_data = {}
    
                    # Collect relevant data for the current cluster
                    for file_key in file_list:
                        if file_key in data_file:  # Ensure the key exists in the source data
                            cluster_data[file_key] = data_file[file_key]
                        else:
                            print(f"Warning: {file_key} not found in source file.")

                    # Write the cluster data to a new JSON file
                    cluster_file_path = os.path.join(destination_directory6, f"{cluster_name}.json")
                    with open(cluster_file_path, 'w', encoding='utf-8') as cluster_file:
                        json.dump(cluster_data, cluster_file, indent=4, ensure_ascii=False)
                    print(f"Cluster {cluster_name} data written to {cluster_file_path}")

                for cluster_name, file_list in node_deno_bun.items():
                    cluster_data = {}
    
                    # Collect relevant data for the current cluster
                    for file_key in file_list:
                        if file_key in data_file:  # Ensure the key exists in the source data
                            cluster_data[file_key] = data_file[file_key]
                        else:
                            print(f"Warning: {file_key} not found in source file.")

                    # Write the cluster data to a new JSON file
                    cluster_file_path = os.path.join(destination_directory7, f"{cluster_name}.json")
                    with open(cluster_file_path, 'w', encoding='utf-8') as cluster_file:
                        json.dump(cluster_data, cluster_file, indent=4, ensure_ascii=False)
                    print(f"Cluster {cluster_name} data written to {cluster_file_path}")
                

                node_only_cluster = {}
                deno_only_cluster = {}
                bun_only_cluster = {}

                node_deno_cluster = {}
                deno_bun_cluster = {}
                node_bun_cluster = {}

                node_deno_bun = {}
            
print("Cluster Done...")

###################################################################### END OF CLUSTER ###########################################################################################################
