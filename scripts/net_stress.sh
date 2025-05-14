#!/bin/bash

start_creating=$(date)

# Deploy server pod
kubectl apply -f /home/cloud_controller_twuttge/scripts/manifests/iperf_server.yaml

# Deploy client pod
kubectl apply -f /home/cloud_controller_twuttge/scripts/manifests/iperf_client.yaml

# Wait for the pods to be ready
kubectl wait --for=condition=Ready pod/iperf-server pod/iperf-client --timeout=120s

finish_creating=$(date)

# Get the IP address of the iperf-server pod
SERVER_IP=$(kubectl get pod iperf-server -o jsonpath='{.status.podIP}')

kubectl exec -i iperf-client -- /bin/sh -c "iperf3 -c $SERVER_IP -p 5201 -t 20"

sleep 5

kubectl exec -i iperf-client -- /bin/sh -c "iperf3 -c $SERVER_IP -p 5201 -P 4 -t 20"

sleep 5

start_deleting=$(date)

# Delete the client pod
kubectl delete pod iperf-client --ignore-not-found
# Delete the server pod
kubectl delete pod iperf-server --ignore-not-found

finish_deleting=$(date)

echo "MEASUREMENT_TIMES: ($finish_creating,$start_deleting)"