#!/bin/bash

input_files="data/papers/order"
output_dir="auto/schedule"

# for timezone in UTC-7; do
#     python2 scripts/order2schedule.py -sec_workshops -order_files_workshops data/workshops/order -output_dir_workshops auto -timezone $timezone
# done

# for timezone in UTC+8; do
    # python2 scripts/order2schedule.py -sec_tutorials -output_dir $output_dir -timezone $timezone -order_files $input_files
# done

# 1- Generate all tex files for all timezone versions
for timezone in UTC-11 UTC-10 UTC-9 UTC-8 UTC-7 UTC-6 UTC-5 UTC-4 UTC-3 UTC-2 UTC-1 UTC+0 UTC+1 UTC+2 UTC+3 UTC+4 UTC+5 UTC+6 UTC+7 UTC+8 UTC+9 UTC+10 UTC+11 UTC+12; do 
    python2 scripts/order2schedule.py -sec_papers -sec_tutorials -sec_workshops -output_dir $output_dir -timezone $timezone -order_files_workshops data/workshops/order -output_dir_workshops auto -order_files $input_files
done

# 2- Compile all tex files for all timezone versions
# for timezone in UTC+0 UTC-7 UTC+8; do 
for timezone in UTC-4 UTC+10 UTC-11 UTC-10 UTC-9 UTC-8 UTC-6 UTC-5 UTC-3 UTC-2 UTC-1 UTC+1 UTC+2 UTC+3 UTC+4 UTC+5 UTC+6 UTC+7 UTC+9 UTC+11 UTC+12; do 
    mkdir -p build_$timezone
    latexmk -pdf -bibtex -output-directory=build_$timezone handbook_$timezone.tex
    mv build_$timezone/handbook_$timezone.pdf ./
    # rm -r build_$timezone
done