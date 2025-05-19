#!/bin/bash

start_testrun=$(date)

sleep 2

# Run CPU benchmark
stress-ng --vm 1 --vm-bytes 80% --timeout 30s

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"