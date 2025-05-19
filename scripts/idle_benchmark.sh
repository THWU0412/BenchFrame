#!/bin/bash

start_testrun=$(date)

# Run idle benchmark
sleep 20

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"