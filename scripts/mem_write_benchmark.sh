#!/bin/bash

start_testrun=$(date)

sleep 2

stress-ng --vm 2 --vm-bytes 75% --vm-method write64 --timeout 30s

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"