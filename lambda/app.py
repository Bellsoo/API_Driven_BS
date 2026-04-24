import json
import os
import boto3

ec2 = boto3.client(
    "ec2",
    endpoint_url="http://localhost.localstack.cloud:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

INSTANCE_ID = os.environ["INSTANCE_ID"]

def handler(event, context):
    path = event.get("path", "")
    method = event.get("httpMethod", "")

    if method != "POST":
        return {"statusCode": 405, "body": json.dumps({"error": "Use POST"})}

    if path.endswith("/start"):
        ec2.start_instances(InstanceIds=[INSTANCE_ID])
        action = "started"
    elif path.endswith("/stop"):
        ec2.stop_instances(InstanceIds=[INSTANCE_ID])
        action = "stopped"
    else:
        return {"statusCode": 404, "body": json.dumps({"error": "Unknown path"})}

    state = ec2.describe_instances(
        InstanceIds=[INSTANCE_ID]
    )["Reservations"][0]["Instances"][0]["State"]["Name"]

    return {
        "statusCode": 200,
        "body": json.dumps({
            "instance_id": INSTANCE_ID,
            "action": action,
            "state": state
        })
    }
