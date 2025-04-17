#!/bin/bash

echo "Start creating: $(date)"
for i in {1..5}; do
  kubectl run nginx-seq-$i \
    --image=nginx \
    --restart=Never
  sleep 5
done
echo "Done creating: $(date)"

sleep 20

echo "Start deleting: $(date)"
for i in {1..5}; do
  kubectl delete pod nginx-seq-$i --ignore-not-found
  sleep 5
done
echo "Done deleting: $(date)"