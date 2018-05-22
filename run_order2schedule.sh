#!/bin/bash

input_files="data/demos/order data/papers/order data/srw/order"
output_dir="auto/papers"

python scripts/order2schedule.py -output_dir $output_dir $input_files
