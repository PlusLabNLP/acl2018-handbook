#!/bin/bash

input_files="data/papers/order data/SRW/order data/demos/order"
output_dir="auto/papers"

python2 scripts/order2schedule.py -output_dir $output_dir $input_files
