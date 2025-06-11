#!/bin/bash

start_testrun=$(date)

logfile="/home/twuttge/net_test/iperf3_server_$(date +"%Y%m%d_%H%M%S").log"
touch "$logfile"

ssh node3 "iperf3 -s -1" | tee -a "$logfile" &

# Wait for the server to start
sleep 2

# Run network benchmark
/home/twuttge/.local/bin/iperf3 -c 192.168.1.103 -t 60 | tee "$logfile"

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
