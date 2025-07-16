import json

with open('./fuzzResults.json') as f:
    d = json.load(f)
    for key in d: 
        roundCounter = 0
        for element in d[key]: 
            roundCounter = roundCounter +1 
        print(roundCounter)