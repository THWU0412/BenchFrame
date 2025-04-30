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
  
  sleep 10
done
echo "Done creating and starting stress tests: $(date)"

echo "Waiting for all stress tests to complete..."

sleep 20

echo "Start deleting: $(date)"
for i in {1..5}; do
  echo "Deleting pod stress-seq-$i..."
  kubectl delete pod stress-seq-$i --ignore-not-found
  sleep 10
done
echo "Done deleting: $(date)"