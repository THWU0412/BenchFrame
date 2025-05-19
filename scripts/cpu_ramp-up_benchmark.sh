#!/bin/bash

start_testrun=$(date)

sleep 2

# Step-wise CPU ramp-up
for cpu_count in 5 10 15 20; do
    end_cpu=$((cpu_count - 1))
    taskset -c 0-"$end_cpu" stress-ng --cpu "$cpu_count" --cpu-method matrixprod --timeout 10s
done

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
