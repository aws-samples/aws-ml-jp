#!/bin/bash

# Check if all required arguments are provided
if [ $# -lt 3 ]; then
  echo "Usage: $0 <instance_id> <region> <port1> <port2> ..."
  exit 1
fi

# Extract instance ID and region from arguments
instance_id=$1
region=$2

# Shift the argument array to exclude instance ID and region
shift 2

# Iterate over the remaining arguments (ports)
while [ $# -gt 0 ]; do
  port=$1

  # Run port forwarding using AWS SSM start-session command
  aws ssm start-session --region "$region" --target "$instance_id" --document-name AWS-StartPortForwardingSession --parameters "{\"portNumber\":[\"$port\"],\"localPortNumber\":[\"$port\"]}" &

  # Shift the argument array to process the next port
  shift
done

# Wait for all port forwarding processes to finish
wait

echo "Port forwarding completed."