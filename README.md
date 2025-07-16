# MASHQ: Differential Testing of JavaScript Runtimes 
This repository contains the prototype used in the evaluation of our paper MASHQ: Differential Testing of JavaScript Runtimes.
MASHQ is designed to apply differential testing against JavaScript runtimes. It requires an input corpus, consisting of several self-contained JavaScript files.

## Artifact Availability 
The associated artifact describes how to run the tool and interpret the results.


## Requirements
We performed the experiments described in the paper on a server with 64 Intel Xeon E5-4650L with 2.60GHz CPU cores and 768GB of memory, and on  12th Gen Intel Core-i9 2.40GHz CPU and 32GB of memory. However, MASHQ does not require specific hardware features, so it can successfully run on other hardware configurations. To replicate the experiments in the artifact, we run MASHQ against the latest versions of these three runtimes at the start of our study: v24.1.0 for Node.js, 2.3.3 for Deno, and 1.2.14 for Bun, on both Linux and Windows machines. However, we successfully run MASHQ in other setups, as well.

## Installation
After cloning the repository, use npm to install all the third-party dependencies in `package.json` by running in the main folder of the project:
```
npm --prefix . install .
```
For the Python packages, we recommend, at first, to use Python3.9 and pip3.9 or higher to install the required packages by running in the main folder of the project: 
```
pip3.9 install -r requirements.txt
```
## TEST SUITE VERSIONS
### V8
 https://chromium.googlesource.com/v8/v8.git/+/refs/heads/main/test/mjsunit/ 
 commit version: https://chromium.googlesource.com/v8/v8.git/+/d8147eb98cacfc65a802b94b3c0dc9cf88f546ab

### TEST262
 https://github.com/tc39/test262/commit/8296db887368bbffa3379f995a1e628ddbe8421f

## Usage
To use MASHQ, you need to run the fuzzer in multiple stages: 
### Tests generation stage
run the following commands: 
```
cd fuzz/testFuzz
node MASHQ -h
```
Here, you will see the options to run the tests generator, for simplicity: 
```
node MASHQ -r 10 -n 4 -N 60 
```
MASHQ will write the generated tests in `${path to the repo}/fuzz/testFuzz/output`

### Running the generated tests
To run the generated tests against Node.js, Deno, and Bun, make sure first that they are all installed with the recommended versions. And then run the following commands: 
```
cd fuzz/testFuzz
python3.9 runFuzzOutputs
```
The test runner will give the results in `${path to the repo}/fuzz/testFuzz/run_outputs`, which is a set of JSON files, showing the logs for each touple of tests. 

### Running the filters
To run the filters against the run outputs, run the following commands: 
```
cd fuzz/testFuzz
python3.9  ../../filters/logFilters.py 
```
The output of running the filters is a set of files/folders, e.g., `panics.json`, `timeouts.json`, and `cluster`  
