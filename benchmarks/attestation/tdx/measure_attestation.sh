#!/bin/bash

# Compile the test_tdx_attest binary
cd /usr/share/doc/libtdx-attest-dev/examples
make > /dev/null

# Number of repetitions
repeats=10
binary="./test_tdx_attest"

total_report_time=0
total_quote_time=0

# Run the binary the specified number of times
for (( i=0; i<$repeats; i++ ))
do
    output=$($binary)
    report_time=$(echo "$output" | grep "Time taken for tdx_att_get_report" | awk '{print $5}')
    quote_time=$(echo "$output" | grep "Time taken for tdx_att_get_quote" | awk '{print $5}')

    total_report_time=$(echo "$total_report_time + $report_time" | bc)
    total_quote_time=$(echo "$total_quote_time + $quote_time" | bc)
done

# Calculate the average times
average_report_time=$(echo "scale=6; $total_report_time / $repeats" | bc)
average_quote_time=$(echo "scale=6; $total_quote_time / $repeats" | bc)

# Print the results in a table format
echo -e "\nAverage Execution Times (in milliseconds) for $repeats repeats:"
printf "%-50s %-10s\n" "Command" "Time (ms)"
printf "%-50s %-10s\n" "-----------------------------" "----------"
printf "%-50s %-10f\n" "tdx_att_get_report" $average_report_time
printf "%-50s %-10f\n" "tdx_att_get_quote" $average_quote_time