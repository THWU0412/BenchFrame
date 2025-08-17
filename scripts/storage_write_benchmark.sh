#!/bin/bash

start_testrun=$(date)

sleep 2

fio --name=write --filename=tmp/testfile --size=2G --bs=4k --rw=write --direct=1 --runtime=30s --time_based --ioengine=posixaio

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
