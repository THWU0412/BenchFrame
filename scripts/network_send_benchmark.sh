#!/bin/bash

start_testrun=$(date)

ssh -i /home/twuttge/.ssh/atlarge twuttge@node3 "iperf3 -s -1" &

# Wait for the server to start
sleep 2

# Run network benchmark
/home/twuttge/.local/bin/iperf3 -c 192.168.1.103 -t 30

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
