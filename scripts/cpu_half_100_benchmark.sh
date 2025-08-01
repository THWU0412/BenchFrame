#!/bin/bash

start_testrun=$(date)

sleep 2

stress-ng --cpu 10 --timeout 30s

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
