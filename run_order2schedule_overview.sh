#!/bin/bash

output_dir="auto/papers"

cat data/{papers,demos,srw}/order | ./scripts/order2schedule_overview.py -output_dir $output_dir
#cat data/{papers,demos}/order | ./scripts/order2schedule_overview.py -output_dir $output_dir
