#!/bin/bash

set -e

echo "Stop de l'instance EC2..."
curl -X POST http://$API_ID.execute-api.localhost.localstack.cloud:4566/dev/ec2/stop
echo

echo "État EC2 après stop :"
awslocal ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].State.Name'

echo "Start de l'instance EC2..."
curl -X POST http://$API_ID.execute-api.localhost.localstack.cloud:4566/dev/ec2/start
echo

echo "État EC2 après start :"
awslocal ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].State.Name'
