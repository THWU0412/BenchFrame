#!/bin/bash

start_testrun=$(date)

sleep 2

# Step-wise CPU ramp-up
for cpu_load in {1..100}; do
    stress-ng --cpu 0 --cpu-load "$cpu_load" --timeout 1s
done

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
