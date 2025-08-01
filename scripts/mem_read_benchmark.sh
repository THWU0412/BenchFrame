#!/bin/bash

start_testrun=$(date)

sleep 2

stress-ng --memrate 1 --memrate-rd-mbs 20000 --memrate-wr-mbs 0 --timeout 60s

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"