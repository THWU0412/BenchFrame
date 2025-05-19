#!/bin/bash

start_testrun=$(date)

# Run network benchmark server
logfile=/home/twuttge/net_test/iperf3_server_$(date +"%d.%m.%Y_%H:%M:%S").log
touch $logfile
/home/twuttge/.local/bin/iperf3 -s -p 5201 --one-off --logfile $logfile

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"