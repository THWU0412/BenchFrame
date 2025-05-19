#!/bin/bash

# echo "Start creating: $(date)"
start_creating=$(date)
for i in {1..2}; do
  # echo "Creating pod stress-mem-$i..."
  kubectl run stress-mem-$i \
    --image=polinux/stress-ng \
    --restart=Never \
    --command -- sleep infinity &
  sleep 5

  # echo "Waiting for pod stress-mem-$i to be ready..."
  kubectl wait --for=condition=Ready pod/stress-mem-$i --timeout=300s

  # echo "Starting stress test inside pod stress-mem-$i..."
  kubectl exec -i stress-mem-$i -- /bin/sh -c 'stress-ng --vm 1 --vm-bytes 3G --timeout 30s' &

  sleep 20
done
finish_creating=$(date)
# echo "Done creating: $(date)"

# echo "Waiting for pods to complete..."

sleep 20

# echo "All pods finished!"

# echo "Start deleting: $(date)"
start_deleting=$(date)
for i in {1..2}; do
  kubectl delete pod stress-mem-$i --ignore-not-found
done
finish_deleting=$(date)
# echo "Done deleting: $(date)"

echo "MEASUREMENT_TIMES: ($finish_creating,$start_deleting)"