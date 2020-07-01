#!/bin/bash

# input_files="data/papers/order data/SRW/order data/demos/order"
input_files="data/papers/order"
output_dir="auto/schedule"
timezone="UTC+8"

python2 scripts/order2schedule.py -output_dir $output_dir -timezone $timezone $input_files
