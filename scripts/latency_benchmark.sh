#!/bin/bash

start_testrun=$(date)

sleep 2

# Linear CPU Load Benchmark
for cpu_load in $(seq 1 20 100); do
    stress-ng --cpu 0 --timeout 2s
    sleep 2
done

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"