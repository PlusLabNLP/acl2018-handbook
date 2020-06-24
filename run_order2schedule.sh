#!/bin/bash

input_files="data/demos/order data/papers/order data/SRW/order"
output_dir="auto/papers"

python2 scripts/order2schedule.py -output_dir $output_dir $input_files
