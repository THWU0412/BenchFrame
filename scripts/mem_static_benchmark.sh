#!/bin/bash

start_testrun=$(date)

# VM stress has a warm up phase, so we run it a bit shorter
stress-ng --vm 2 --vm-bytes 75% --timeout 28s

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"