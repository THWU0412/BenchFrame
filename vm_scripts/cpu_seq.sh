#!/bin/bash

# Source for polinux/stress-ng:
# https://medium.com/@email2smohanty/stress-testing-kubernetes-k8s-and-openshift-nodes-using-stress-ng-35b6a9752c8d

# Source for k8s-pod-cpu-stressor:
# https://dev.to/narmidm/introducing-k8s-pod-cpu-stressor-simplify-cpu-load-testing-in-kubernetes-1629

NUM_PODS=5
start_creating=$(date)

for i in $(seq 1 "$NUM_PODS"); do
  kubectl run stress-seq-$i \
    --image=polinux/stress-ng \
    --restart=Never \
    --command -- sleep infinity

  kubectl wait --for=condition=Ready pod/stress-seq-$i --timeout=60s
done
finish_creating=$(date)
# echo "Start test"

for i in $(seq 1 "$NUM_PODS"); do
  echo "Running pod stress-seq-$i"
  kubectl exec -i stress-seq-$i -- /bin/sh -c 'stress-ng --cpu 2 --timeout 60s' &
  sleep 10
done

wait
# echo "All pods finished!"

sleep 10

start_deleting=$(date)
for i in $(seq 1 "$NUM_PODS"); do
  kubectl delete pod stress-seq-$i --ignore-not-found
  kubectl wait --for=delete pod/stress-seq-$i --timeout=60s
done

finish_deleting=$(date)
echo "MEASUREMENT_TIMES: ($finish_creating,$start_deleting)"