#!/bin/bash

# Set the path to your Python script
python_script="TimeScanParallelSlice.py"

# Specify the parameters
threshold=0
special_params="--special parity,positive"

# Execute the Python script with the given parameters
run_number=286
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
run_number=216
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
run_number=274
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
run_number=260
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
run_number=261
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
run_number=266
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
run_number=262
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
run_number=267
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
run_number=263
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
run_number=268
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
run_number=269
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
run_number=264
python "$python_script" -r "$run_number" --threshold "$threshold" "$special_params"
