#!/bin/bash

# Source:
# https://medium.com/@email2smohanty/stress-testing-kubernetes-k8s-and-openshift-nodes-using-stress-ng-35b6a9752c8d

# echo "Start creating: $(date)"
start_creating=$(date)
for i in {1..5}; do
  # echo "Creating pod stress-seq-$i..."
  kubectl run stress-seq-$i \
    --image=polinux/stress-ng \
    --restart=Never \
    --command -- sleep infinity

  # echo "Waiting for pod stress-seq-$i to be ready..."
  kubectl wait --for=condition=Ready pod/stress-seq-$i --timeout=300s

  # echo "Starting stress test inside pod stress-seq-$i..."
  kubectl exec -it stress-seq-$i -- /bin/sh -c 'stress-ng --cpu 2 --timeout 30s'
  
  sleep 10
done
finish_creating=$(date)
# echo "Done creating and starting stress tests: $(date)"

# echo "Waiting for all stress tests to complete..."

sleep 20

start_deleting=$(date)
# echo "Start deleting: $(date)"
for i in {1..5}; do
  # echo "Deleting pod stress-seq-$i..."
  kubectl delete pod stress-seq-$i --ignore-not-found
  kubectl wait --for=delete pod/stress-seq-$i --timeout=60s
  sleep 10
done
# echo "Done deleting: $(date)"
finish_deleting=$(date)
echo "MEASUREMENT_TIMES: ($finish_creating,$start_deleting)"