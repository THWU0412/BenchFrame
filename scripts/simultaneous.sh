#!/bin/bash

echo "Start creating: $(date)"
for i in {1..5}; do
  echo "Creating pod stress-seq-$i..."
  kubectl run stress-seq-$i \
    --image=polinux/stress-ng \
    --restart=Never \
    --command -- sleep infinity

  echo "Waiting for pod stress-seq-$i to be ready..."
  kubectl wait --for=condition=Ready pod/stress-seq-$i --timeout=60s

  echo "Starting stress test inside pod stress-seq-$i..."
  kubectl exec -it stress-seq-$i -- /bin/sh -c 'stress-ng --cpu 2 --timeout 60s' &
done
echo "Done creating: $(date)"

echo "Waiting for pods to complete..."

sleep 70

echo "All pods finished!"

echo "Start deleting: $(date)"
for i in {1..5}; do
  kubectl delete pod stress-seq-$i --ignore-not-found
done
echo "Done deleting: $(date)"