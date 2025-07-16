import json
import os

cwd = "../fuzz/testFuzz/run_outputs/" #os.getcwd()
source = os.path.join(cwd,"fuzzResults.json")

panic_file = os.path.join(cwd,"panic.json") 
timeout_file = os.path.join(cwd,"timeout.json")
same_error_file = os.path.join(cwd,"same_error.json")
sameoutput_file = os.path.join(cwd,"sameoutput.json")
diff_error_file = os.path.join(cwd,"differror.json")

keywords = ["ReferenceError:", "TypeError:", "SyntaxError:", "Test262Error"]

panic_flag = False 
timeout_flag = False 
same_error_flag = False 
sameoutput_flag = False 
#address_in_use_flag = False 

# Load the fuzz_stats.json file
with open(source, 'r') as source_file:
    round_data = json.load(source_file)

timeout_logs = {}
remaining_logs = {}
same_error_logs = {}
panic_logs = {}
sameoutput_logs = {}

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

    }
    
    for key, log in data.items():
        print(round, "    ", key)
        timeout_flag = False
        same_error_flag = False 
        panic_flag = False
        sameoutput_flag = False 
        #address_in_use_flag = False  

        node_log = log.get('node', '').strip()
        deno_log = log.get('deno', '').strip()
        bun_log = log.get('bun', '').strip()

        '''
        if "panic" in deno_log or "segFault" in node_log or "panic" in bun_log:
            #panic_logs[key] = log 
            panic_flag = True 

            if "panic" in deno_log: 
                round_stats["panics"]["deno"] = round_stats["panics"]["deno"] + 1
            if  "panic" in node_log:
                round_stats["panics"]["node"] = round_stats["panics"]["node"] + 1
            if "panic" in bun_log: 
                round_stats["panics"]["bun"] = round_stats["panics"]["bun"] + 1
        '''
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
        else:
            if round not in remaining_logs.keys(): 
                remaining_logs[round] = {}
            remaining_logs[round][key] = log 
        
        stats[round] = round_stats


# Write logs to op files 
with open(timeout_file, 'w') as dest_file:
    json.dump(timeout_logs, dest_file, indent=4)

with open(panic_file, 'w') as dest_file:
    json.dump(panic_logs, dest_file, indent=4)

with open(same_error_file, 'w') as dest_file:
    json.dump(same_error_logs, dest_file, indent=4)

with open(sameoutput_file, 'w') as dest_file:
    json.dump(sameoutput_logs, dest_file, indent=4)

with open(diff_error_file, 'w') as dest_file:
    json.dump(remaining_logs, dest_file, indent=4)




print(stats)

print(f"\nDone\n")


