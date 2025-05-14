#!/bin/bash

NUM_PODS=5

start_creating=$(date)

for i in $(seq 1 "$NUM_PODS"); do
  kubectl run stress-sim-$i \
    --image=polinux/stress-ng \
    --restart=Never \
    --command -- sleep infinity

  kubectl wait --for=condition=Ready pod/stress-sim-$i --timeout=300s
done
finish_creating=$(date)

# echo "Start test"

for i in $(seq 1 "$NUM_PODS"); do
  kubectl exec -i stress-sim-$i -- /bin/bash -c "stress-ng --cpu 4 --timeout 60s" &
done

wait 

# echo "All pods finished!"

sleep 10

start_deleting=$(date)
for i in $(seq 1 "$NUM_PODS"); do
  kubectl delete pod stress-sim-$i --ignore-not-found
  kubectl wait --for=delete pod/stress-sim-$i --timeout=60s
done
finish_deleting=$(date)

echo "MEASUREMENT_TIMES: ($finish_creating,$start_deleting)"