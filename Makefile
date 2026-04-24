test-api:
	./scripts/test-api.sh

status:
	awslocal ec2 describe-instances --instance-ids $$INSTANCE_ID --query 'Reservations[0].Instances[0].State.Name'

start:
	curl -X POST http://$$API_ID.execute-api.localhost.localstack.cloud:4566/dev/ec2/start

stop:
	curl -X POST http://$$API_ID.execute-api.localhost.localstack.cloud:4566/dev/ec2/stop
