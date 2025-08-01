#!/bin/bash

start_testrun=$(date)

sleep 2

fio --name=read_test --filename=tmp/testfile_read --bs=4k --rw=randread --direct=1 --iodepth=256 --numjobs=1 --runtime=30s --time_based --ioengine=posixaio --readonly

sleep 2

end_testrun=$(date)

echo "MEASUREMENT_TIMES: ($start_testrun,$end_testrun)"
