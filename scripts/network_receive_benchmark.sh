#!/bin/bash

start_testrun=$(date)

ssh -i "$3" "$1@$2" "iperf3 -s -1" &

# Wait for the server to start
sleep 2

# Run network benchmark
iperf3 -c 192.168.1.103 -t 30 -R

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
