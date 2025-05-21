#!/bin/bash

start_testrun=$(date)

sleep 2

# Run CPU benchmark
stress-ng --vm 2 --vm-bytes 80% --timeout 60s

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"