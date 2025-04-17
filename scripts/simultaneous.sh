#!/bin/bash

echo "Start creating: $(date)"
for i in {1..10}; do
  kubectl run nginx-$i \
    --image=nginx \
    --restart=Never
done
echo "Done creating: $(date)"

sleep 20

echo "Start deleting: $(date)"
for i in {1..10}; do
  kubectl delete pod nginx-$i --ignore-not-found
done
echo "Done deleting: $(date)"