#!/bin/bash

# input_files="data/papers/order data/SRW/order data/demos/order"
input_files="data/papers/order"
output_dir="auto/schedule"

python2 scripts/order2schedule.py -output_dir $output_dir $input_files
