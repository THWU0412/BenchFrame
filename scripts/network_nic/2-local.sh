#!/bin/bash

start_testrun=$(date)

# Run network benchmark
logfile=/home/twuttge/net_test/iperf3_server_$(date +"%Y%m%d_%H%M%S").log
touch $logfile
iperf3 -c 192.168.1.109 -t 60 --logfile "$logfile"

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"