#!/bin/bash

# echo "Start creating: $(date)"
start_creating=$(date)
for i in {1..5}; do
  # echo "Creating pod stress-sim-$i..."
  kubectl run stress-sim-$i \
    --image=polinux/stress-ng \
    --restart=Never \
    --command -- sleep infinity

  # echo "Waiting for pod stress-sim-$i to be ready..."
  kubectl wait --for=condition=Ready pod/stress-sim-$i --timeout=300s

  # echo "Starting stress test inside pod stress-sim-$i..."
  kubectl exec -it stress-sim-$i -- /bin/sh -c 'stress-ng --cpu 2 --timeout 60s' &
done
finish_creating=$(date)
# echo "Done creating: $(date)"

# echo "Waiting for pods to complete..."

sleep 70

# echo "All pods finished!"

# echo "Start deleting: $(date)"
start_deleting=$(date)
for i in {1..5}; do
  kubectl delete pod stress-sim-$i --ignore-not-found
done
finish_deleting=$(date)
# echo "Done deleting: $(date)"

echo "MEASUREMENT_TIMES: ($finish_creating,$start_deleting)"