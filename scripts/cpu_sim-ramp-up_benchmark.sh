#!/bin/bash

start_testrun=$(date)

sleep 2

# Step-wise CPU ramp-up
for cpu_load in 25 50 75 100; do
    stress-ng --cpu 0 --cpu-load "$cpu_load" --timeout 15s
done

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
