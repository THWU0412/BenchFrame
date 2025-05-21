#!/bin/bash

start_testrun=$(date)

sleep 2

# Linear CPU Load Benchmark
# This does not really work because it is shit
for cpu_load in $(seq 1 5 100); do
    stress-ng --cpu 0 --cpu-load "$cpu_load" --timeout 5s
done
done

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
