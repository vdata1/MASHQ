#filter4_optimized is the one before this
from collections import OrderedDict
import spacy
from nltk.corpus import stopwords

import os
import json
import shutil

import re 

nlp = spacy.load("en_core_web_md")
stop_words = set(stopwords.words("english"))

cwd = os.getcwd()
source = os.path.join(cwd,"separated",'differror.json')
destination_folder = os.path.join(cwd,'filtered_op.json')
remaining_folder = os.path.join(cwd,"remaining.json")

#os.makedirs(destination_folder, exist_ok=True)

def error_similarity(statement1, statement2):
    # Process the two error statements
    doc1 = nlp(statement1)
    doc2 = nlp(statement2)
    
    # Calculate similarity
    similarity = doc1.similarity(doc2)
    return similarity*100
    #return round(similarity * 100, 2)  

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

def extract_error_string(stderr):
    start_token = 'error:'
    start_idx = stderr.find(start_token)
    if start_idx != -1:
        start_idx += len(start_token)
        end_idx = stderr.find('\n', start_idx)
        if end_idx != -1:
            return stderr[start_idx:end_idx].strip()
    return None

def check_error_in_stderr(stderr, error_str):
    return error_str.lower() in stderr.lower()

def move_file(file_path,filename,destination_folder):
    shutil.move(file_path, os.path.join(destination_folder, filename))
    print(f"Moved {filename} to {destination_folder}")



with open(source, 'r') as source_file:
    round_data = json.load(source_file)

filter_logs = {}
remaining_logs = {} 

for round, data in round_data.items():
    print("processing: ", round)
    for key, log in data.items():

            node_stderr = log.get('node', '').strip()
            deno_stderr = log.get('deno', '').strip()
            bun_stderr = log.get('bun', '').strip()
            error_str = extract_error_string(bun_stderr)

            move = False

            #low level filter 1
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"error") and check_error_in_stderr(bun_stderr,"error:")):
            
                
                #filter1
                if check_error_in_stderr(node_stderr,"Cannot use"):
                    if check_error_in_stderr(node_stderr,"import"):
                        if check_error_in_stderr(deno_stderr,"import is not allowed"):
                            if check_error_in_stderr(bun_stderr,"Cannot") and check_error_in_stderr(bun_stderr,"import"):
                                move = True

                    if check_error_in_stderr(node_stderr,"outside a module"):
                        if check_error_in_stderr(deno_stderr,"Invalid destructuring"):
                            if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                                move = True

                    if check_error_in_stderr(node_stderr,"outside a module"):
                        if check_error_in_stderr(deno_stderr,"Invalid left-hand"):
                            if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                                move = True

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

                #filter4
                if check_error_in_stderr(node_stderr,"Invalid destructuring"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                            move = True

                #filter5
                if check_error_in_stderr(node_stderr,"Invalid left-hand"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                #filter6
                if check_error_in_stderr(node_stderr,"Invalid left-hand"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                            move = True

                #filter7
                if check_error_in_stderr(node_stderr,"Lexical declaration"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"single-statement context"):
                            move = True

                #filter8
                if check_error_in_stderr(node_stderr,"Malformed arrow function"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                #filter9
                if check_error_in_stderr(node_stderr,"require a function name"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                #filter10
                if check_error_in_stderr(node_stderr,"reserved word"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"cannot be named") or check_error_in_stderr(bun_stderr,"Cannot use"):
                            move = True

                #filter11
                if check_error_in_stderr(node_stderr,"strict mode") and check_error_in_stderr(node_stderr,"reserved word"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr("parsed"):
                        if check_error_in_stderr(bun_stderr,"reserved word"):
                            move = True
        
                #filter12
                if check_error_in_stderr(node_stderr,"super") and check_error_in_stderr(node_stderr,"keyword unexpected"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr("parsed"):
                        if check_error_in_stderr(bun_stderr,"Unexpected") and check_error_in_stderr(bun_stderr,"super"):
                            move = True

                #filter13
                if check_error_in_stderr(node_stderr,"tagged template"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr("parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                #filter14
                if check_error_in_stderr(node_stderr,"Unary operator"):
                    if check_error_in_stderr(deno_stderr,"unary/await"):
                        if check_error_in_stderr(bun_stderr,"Unexpected"):
                            move = True

                #filter15
                if check_error_in_stderr(node_stderr,"Unexpected end of input"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                #filter16
                if check_error_in_stderr(node_stderr,"Unexpected string"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

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

                #filter18
                if check_error_in_stderr(node_stderr,"Yield expression"):
                    if check_error_in_stderr(deno_stderr,"yield") and check_error_in_stderr(deno_stderr,"cannot be used"):
                        if check_error_in_stderr(bun_stderr,"yield") and check_error_in_stderr(bun_stderr,"cannot be used"):
                            move = True
            #low level filter 2
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"SyntaxError:") and check_error_in_stderr(bun_stderr,"error:")):    

                #filter19 
                if check_error_in_stderr(node_stderr,"arguments") and check_error_in_stderr(node_stderr,"not allowed"):
                    if check_error_in_stderr(deno_stderr,"arguments") and check_error_in_stderr(deno_stderr,"not allowed"):
                        if check_error_in_stderr(bun_stderr,"Cannot access"):
                            move = True

                #filter20
                if check_error_in_stderr(node_stderr,"can only be declared"):
                    if check_error_in_stderr(deno_stderr,"can only be declared"):
                        if check_error_in_stderr(bun_stderr,"single-statement context"):
                            move = True

                #filter21
                if check_error_in_stderr(node_stderr,"escaped characters"):
                    if check_error_in_stderr(deno_stderr,"escaped characters"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True			

                #filter22
                if check_error_in_stderr(node_stderr,"for-await-of"):
                    if check_error_in_stderr(deno_stderr,"for-await-of"):
                        if check_error_in_stderr(bun_stderr,"for-of"):
                            move = True

                #filter23
                if check_error_in_stderr(node_stderr,"Generators") and check_error_in_stderr(node_stderr,"declared"):
                    if check_error_in_stderr(deno_stderr,"strict mode"):
                        if check_error_in_stderr(bun_stderr,"single-statement context"):
                            move = True

                #filter24
                if check_error_in_stderr(node_stderr,"Getter") and check_error_in_stderr(node_stderr,"formal parameters"):
                    if check_error_in_stderr(deno_stderr,"Getter") and check_error_in_stderr(node_stderr,"formal parameters"):
                        if check_error_in_stderr(bun_stderr,"Getter") and check_error_in_stderr(bun_stderr,"zero arguments"):
                            move = True

                #filter25
                if check_error_in_stderr(node_stderr,"Illegal"):
                    if check_error_in_stderr(deno_stderr,"Illegal"):
                        if check_error_in_stderr(bun_stderr,"cannot be used here"):
                            move = True

                #filter26
                if check_error_in_stderr(node_stderr,"Illegal break"):
                    if check_error_in_stderr(deno_stderr,"Illegal break"):
                        if check_error_in_stderr(bun_stderr,"Cannot use") and check_error_in_stderr(bun_stderr,"break"):
                            move = True
                
                #filter27
                if check_error_in_stderr(node_stderr,"Illegal continue"):
                    if check_error_in_stderr(deno_stderr,"Illegal continue"):
                        if check_error_in_stderr(bun_stderr,"Cannot use") and check_error_in_stderr(bun_stderr,"continue"):
                            move = True

                #filter28
                if check_error_in_stderr(node_stderr,"Invalid left-hand"):
                    if check_error_in_stderr(deno_stderr,"Invalid left-hand"):
                        if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                            move = True

                #filter29
                if check_error_in_stderr(node_stderr,"Invalid shorthand"):
                    if check_error_in_stderr(deno_stderr,"Invalid shorthand"):
                        if check_error_in_stderr(bun_stderr,"Unexpected"):
                            move = True

                #filter30
                if check_error_in_stderr(node_stderr,"is disallowed"):
                    if check_error_in_stderr(deno_stderr,"strict mode"):
                        if check_error_in_stderr(bun_stderr,"Cannot use"):
                            move = True

                #filter31
                if check_error_in_stderr(node_stderr,"Missing") and check_error_in_stderr(node_stderr,"catch") and check_error_in_stderr(node_stderr,"finally"):
                    if check_error_in_stderr(deno_stderr,"Missing") and check_error_in_stderr(deno_stderr,"catch") and check_error_in_stderr(deno_stderr,"finally"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                #filter32
                if check_error_in_stderr(node_stderr,"not a valid identifier name"):
                    if check_error_in_stderr(deno_stderr,"Unexpected token"):
                        if check_error_in_stderr(bun_stderr,"Unexpected"):
                            move = True

                #filter33
                if check_error_in_stderr(node_stderr,"Private field"):
                    if check_error_in_stderr(deno_stderr,"Private field"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"Private name"):
                            move = True 

                #filter34
                if check_error_in_stderr(node_stderr,"Private fields"):
                    if check_error_in_stderr(deno_stderr,"Private fields"):
                        if check_error_in_stderr(bun_stderr,"Private name"):
                            move = True

                #filter35
                if check_error_in_stderr(node_stderr,"regular expression"):
                    if check_error_in_stderr(deno_stderr,"regular expression"):
                        if check_error_in_stderr(bun_stderr,"regular expression"):
                            move = True

                #filter36
                if check_error_in_stderr(node_stderr,"reserved word"):
                    if check_error_in_stderr(deno_stderr,"reserved word"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                #filter37
                if check_error_in_stderr(node_stderr,"Rest element"):
                    if check_error_in_stderr(deno_stderr,"Rest element"):
                        if check_error_in_stderr(bun_stderr,"rest pattern"):
                            move = True

                #filter38
                if check_error_in_stderr(node_stderr,"static property"):
                    if check_error_in_stderr(deno_stderr,"static property"):
                        if check_error_in_stderr(bun_stderr,"Invalid field name") or check_error_in_stderr(bun_stderr,"static method"):
                            move = True

                #filter39
                if check_error_in_stderr(node_stderr,"strict mode"):
                    if check_error_in_stderr(deno_stderr,"strict mode"):
                        if check_error_in_stderr(bun_stderr,"single-statement context"):
                            move = True

                #filter40
                if check_error_in_stderr(node_stderr,"tagged template"):
                    if check_error_in_stderr(deno_stderr,"tagged template"):
                        if check_error_in_stderr(bun_stderr,"template literals"):
                            move = True

                #filter41
                if check_error_in_stderr(node_stderr,"top level bodies"):
                    if check_error_in_stderr(deno_stderr,"reserved word"):
                        if check_error_in_stderr(bun_stderr,"can only be used"):
                            move = True

                #filter42
                if check_error_in_stderr(node_stderr,"Undefined label"):
                    if check_error_in_stderr(deno_stderr,"Undefined label"):
                        if check_error_in_stderr(bun_stderr,"containing label"):
                            move = True

                #filter43
                if check_error_in_stderr(node_stderr,"Unexpected eval"):
                    if check_error_in_stderr(deno_stderr,"Unexpected eval"):
                        if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"target"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"cannot be used"):
                            move = True

                #filter44
                if check_error_in_stderr(node_stderr,"Unexpected identifier"):
                    if check_error_in_stderr(deno_stderr,"reserved word"):
                        if check_error_in_stderr(bun_stderr,"cannot be escaped") or check_error_in_stderr(bun_stderr,"Cannot use"):
                            move = True

                #filter45
                if check_error_in_stderr(node_stderr,"Unexpected number"):
                    if check_error_in_stderr(deno_stderr,"reserved word"):
                        if check_error_in_stderr(bun_stderr,"can only be used"):
                            move = True

                #filter46
                if check_error_in_stderr(node_stderr,"Unexpected string"):
                    if check_error_in_stderr(deno_stderr,"Unexpected string"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True

                #filter47
                if check_error_in_stderr(node_stderr,"Unexpected token"):
                    if check_error_in_stderr(deno_stderr,"Unexpected token"):
                        if check_error_in_stderr(bun_stderr,"Expected") and check_error_in_stderr(bun_stderr,"found"):
                            move = True
                        elif check_error_in_stderr(bun_stderr,"Unexpected"):
                            move = True

            #low level filter 3 
            if (check_error_in_stderr(node_stderr,"Error ") and check_error_in_stderr(deno_stderr,"TypeError:") and check_error_in_stderr(bun_stderr,"error:")):
                
                #filter48   
                if check_error_in_stderr(node_stderr,"Cannot find module"):
                    if check_error_in_stderr(deno_stderr,"Module not found"):
                        if check_error_in_stderr(bun_stderr,"Cannot find module"):
                            move = True

                #filter49
                if check_error_in_stderr(node_stderr,"Cannot find package"):
                    if check_error_in_stderr(deno_stderr,"TypeError"):
                        if check_error_in_stderr(bun_stderr,"Cannot find package"):
                            move = True

            #low level filter 4 
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"error") and check_error_in_stderr(bun_stderr,"SyntaxError:")):
            
                #filter50
                if check_error_in_stderr(node_stderr,"for-in"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"for-in"):
                            move = True
                
                #filter51
                if check_error_in_stderr(node_stderr,"reserved word"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Cannot declare"):
                            move = True

            #low level filter 5
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"error") and check_error_in_stderr(bun_stderr,"error:") and check_error_in_stderr(bun_stderr,"Syntax Error")):

                #filter52
                if check_error_in_stderr(node_stderr,"regular expression"):
                    if check_error_in_stderr(deno_stderr,"regexp literal"):
                        if check_error_in_stderr(bun_stderr,"Syntax Error"):
                            move = True

                #filter53
                if check_error_in_stderr(node_stderr,"unexpected token"):
                    if check_error_in_stderr(deno_stderr,"module") and check_error_in_stderr(deno_stderr,"parsed"):
                        if check_error_in_stderr(bun_stderr,"Syntax Error"):
                            move = True

            #low level filter 6 
            if error_str:
                if check_error_in_stderr(node_stderr,"Test262Error") and check_error_in_stderr(deno_stderr,"Test262Error"):
                    if check_error_in_stderr(node_stderr,error_str) and check_error_in_stderr(deno_stderr,error_str):
                        move = True

            #filter54
            if (check_error_in_stderr(node_stderr,"EADDRINUSE") and check_error_in_stderr(deno_stderr,"AddrInUse") and check_error_in_stderr(bun_stderr,"EADDRINUSE")):
                move = True

            #low level filter 6
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"SyntaxError:") and check_error_in_stderr(bun_stderr,"Syntax Error")):
                move = True

            #low level filter 7
            if (check_error_in_stderr(node_stderr,"SyntaxError:") and check_error_in_stderr(deno_stderr,"SyntaxError") and check_error_in_stderr(deno_stderr,"error") and check_error_in_stderr(bun_stderr,"error:")):
                
                #filter55
                if check_error_in_stderr(node_stderr,"Invalid") and check_error_in_stderr(node_stderr,"unexpected") and check_error_in_stderr(node_stderr,"token"):
                    if check_error_in_stderr(deno_stderr,"Invalid") and check_error_in_stderr(deno_stderr,"unexpected") and check_error_in_stderr(deno_stderr,"token"):
                        if check_error_in_stderr(bun_stderr,"Invalid") and check_error_in_stderr(bun_stderr,"identifier"):
                            move = True

            if check_error_in_stderr(node_stderr,"subprocess killed"):
                if check_error_in_stderr(deno_stderr,"process killed"):
                    if check_error_in_stderr(bun_stderr,"subprocess killed"):
                        move = True 

            #low level filter 8
            if check_error_in_stderr(node_stderr,"Server running at"):
                if check_error_in_stderr(deno_stderr,"Server running at"):
                    if check_error_in_stderr(bun_stderr,"Server running at"):
                        move = True

            #dynamic filter
            node_refined = preprocess_error(node_stderr)
            node_refined = extract_meaningful_error_message_node(node_refined)

            deno_refined = preprocess_error(deno_stderr)
            deno_refined = extract_meaningful_error_message_deno(deno_refined)
            
            bun_refined = preprocess_error(bun_stderr)
            bun_refined = extract_meaningful_error_message_node(bun_refined)
            bun_refined = re.sub(r"[^\x00-\x7F]+", "",bun_refined)
            
            if error_similarity(node_refined,deno_refined) >= 90:
                if error_similarity(deno_refined,bun_refined) >=92:
                    if error_similarity(node_refined,bun_refined)>=90:
                        move = True

            if move:
                #move_file(file_path,filename,destination_folder)
                filter_logs[key] = log 
            else:
                remaining_logs[key] = log 


    with open(os.path.join(cwd, f'{round}_filtered_op.json'), 'w') as dest_file:
        json.dump(filter_logs, dest_file, indent=4)

    with open(os.path.join(cwd,f'{round}_remaining.json'), 'w') as dest_file:
        json.dump(remaining_logs, dest_file, indent=4)

    
    filter_logs = {}
    remaining_logs = {} 





























































