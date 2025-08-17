#!/bin/bash

start_testrun=$(date)

sleep 2

fio --name=read --filename=tmp/testfile --bs=4k --rw=read --direct=1 --iodepth=256 --numjobs=1 --runtime=30s --time_based --ioengine=posixaio --readonly

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
