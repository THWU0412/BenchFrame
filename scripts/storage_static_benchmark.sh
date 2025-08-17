#!/bin/bash

start_testrun=$(date)

sleep 2

fio --name=static --filename=tmp/testfile --size=2G --bs=1024k --rw=readwrite --direct=1 --iodepth=256 --numjobs=1 --runtime=30s --time_based

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
