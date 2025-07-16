import os 
import json

temp = {} 

def file_counter_filtered(filename,data):
    print(os.path.basename(filename)," : ",len(data),)

    
def file_counter(filename,data):
    if os.path.basename(filename) == "timeout.json" or os.path.basename(filename) == "panic.json":  
        print("Total file-count for each round in", os.path.basename(filename))
    else:
        print(os.path.basename(filename))
    temp = {}
    for round_name, files in data.items():
        file_count = len(files.keys())
        print(f"{round_name}: {file_count} files")
        temp[round_name] = file_count
    return temp

def file_counter_pt(filename,data):
    print("Separated round-wise panic count in", os.path.basename(filename))
    temp = {}
    for round_name, files in data.items():
      
        node_sum = 0
        deno_sum = 0
        bun_sum = 0

        for file_name, content in files.items():
            node_result = content.get("node", "No node result found")
            deno_result = content.get("deno", "No deno result found")
            bun_result = content.get("bun", "No bun result found")

            node_result = node_result.lower()
            deno_result = deno_result.lower()
            bun_result = bun_result.lower()

            if "panic" in node_result or "fatal error" in node_result or "core dumped" in node_result:
                node_sum += 1
            if "panic" in deno_result or "fatal error" in deno_result or "core dumped" in deno_result:
                deno_sum += 1
            if "panic" in bun_result or "fatal error" in bun_result or "core dumped" in bun_result:
                bun_sum += 1
        
        #print()
        temp[round_name] = {"node":node_sum,"deno":deno_sum,"bun":bun_sum}

    for round_name, results in temp.items():
        print(f"{round_name}:")
        for key, value in results.items():
            print(f"    {key}: {value}")

    return temp

def file_counter_pt2(filename,data):
    print("Separated round-wist timeout count in", os.path.basename(filename))
    temp = {}
    for round_name, files in data.items():
      
        node_sum = 0
        deno_sum = 0
        bun_sum = 0

        for file_name, content in files.items():
            node_result = content.get("node", "No node result found")
            deno_result = content.get("deno", "No deno result found")
            bun_result = content.get("bun", "No bun result found")

            node_result = node_result.lower()
            deno_result = deno_result.lower()
            bun_result = bun_result.lower()

            if "timeout" in node_result:
                node_sum += 1
            if "timeout" in deno_result:
                deno_sum += 1
            if "timeout" in bun_result:
                bun_sum += 1
        
        #print()
        temp[round_name] = {"node":node_sum,"deno":deno_sum,"bun":bun_sum}

    for round_name, results in temp.items():
        print(f"{round_name}:")
        for key, value in results.items():
            print(f"    {key}: {value}")

    return temp

cwd = os.getcwd()
filtered_folder = os.path.join(cwd,"filtered") 
total = os.path.join(cwd,"fuzzResults.json")
diff_error = os.path.join(cwd,"separated","differror.json")
dynamic_sameerror = os.path.join(cwd,"separated","dynamic_samerror.json")
panic = os.path.join(cwd,"separated","panic.json")
same_error = os.path.join(cwd,"separated","same_error.json")
sameoutput = os.path.join(cwd,"separated","sameoutput.json")
timeout = os.path.join(cwd,"separated","timeout.json")


#output_file = os.path.join(base_directory,"fuzzResults.json")

with open(diff_error, 'r', encoding='utf-8') as file:
    data1 = json.load(file)

with open(dynamic_sameerror, 'r', encoding='utf-8') as file:
    data2 = json.load(file)

with open(panic, 'r', encoding='utf-8') as file:
    data3 = json.load(file)

with open(same_error, 'r', encoding='utf-8') as file:
    data4 = json.load(file)

with open(sameoutput, 'r', encoding='utf-8') as file:
    data5 = json.load(file)

with open(timeout, 'r', encoding='utf-8') as file:
    data6 = json.load(file)

with open(total, 'r', encoding='utf-8') as file:
    data7 = json.load(file)


total_dict = {}
dynamic_same_dict = {}
timeout_dict = {}
panic_dict = {}
same_error_dict = {}
same_op_dict = {}
diff_error_dict = {}

total_dict = file_counter(total,data7)
print("\n")
dynamic_same_dict = file_counter(dynamic_sameerror,data2)
print("\n")
timeout_dict = file_counter_pt2(timeout,data6)
timeout_dict_for_sum = file_counter(timeout,data6)
print("\n")
panic_dict = file_counter_pt(panic,data3)
panic_dict_for_sum = file_counter(panic,data3)
print("\n")
same_error_dict = file_counter(same_error,data4)
print("\n")
same_op_dict = file_counter(sameoutput,data5)
print("\n")
diff_error_dict = file_counter(diff_error,data1)
print("\n")

for i in total_dict.keys():
    sum = 0
    if i in dynamic_same_dict:
        sum += dynamic_same_dict[i]
    if i in timeout_dict_for_sum:
        sum += timeout_dict_for_sum[i]
    if i in panic_dict_for_sum:
        sum += panic_dict_for_sum[i]
    if i in same_error_dict:
        sum += same_error_dict[i]
    if i in same_op_dict:
        sum += same_op_dict[i]
    if i in diff_error_dict:
        sum += diff_error_dict[i]
    if sum == total_dict[i]:
        print(i,"sum is matching")
    else:
        print(i,"sum is NOT matching")

###########################################################################

print("\n")

file_count = len([f for f in os.listdir(filtered_folder) if os.path.isfile(os.path.join(filtered_folder, f))])
file_count = file_count/2
#print(file_count)

filter_dict = {}
remaining_dict = {}

for i in range(1,int(file_count)+1):
    f = os.path.join(cwd,"filtered","round_"+str(i)+"_filtered_op.json")
    r = os.path.join(cwd,"filtered","round_"+str(i)+"_remaining.json")

    with open(f, 'r', encoding='utf-8') as file:
        fdata = json.load(file)
    with open(r, 'r', encoding='utf-8') as file:
        rdata = json.load(file)

    file_counter_filtered(f,fdata)
    file_counter_filtered(r,rdata)

    filter_dict["round_"+str(i)] = len(fdata)
    remaining_dict["round_"+str(i)] = len(rdata)
    
    print("\n")

for i in diff_error_dict.keys():
    sum = 0
    if i in filter_dict:
        sum += filter_dict[i]
    if i in remaining_dict:
        sum += remaining_dict[i]
    if sum == diff_error_dict[i]:
        print(i,"sum is matching")
    else:
        print(i,"sum is NOT matching")


