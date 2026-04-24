## Séquence 1 — GitHub Codespaces
Objectif

Créer un environnement de travail en ligne.

Le projet a été ouvert dans GitHub Codespaces afin de disposer :

d’un terminal Linux
de Python
de Git
d’un environnement prêt à coder
## Séquence 2 — Mise en place de LocalStack
Objectif

Créer un environnement AWS simulé.

Installation
sudo -i mkdir rep_localstack
sudo -i python3 -m venv ./rep_localstack
sudo -i pip install --upgrade pip && python3 -m pip install localstack && export S3_SKIP_SIGNATURE_VALIDATION=0
Démarrage
localstack start -d
Vérification
localstack status services
Variables d’environnement

Avant d’utiliser AWS CLI et GitHub :

export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export GITHUB_TOKEN=VOTRE_TOKEN

Si besoin de LocalStack Pro :

export LOCALSTACK_AUTH_TOKEN=VOTRE_TOKEN
Installation des outils CLI
pip install awscli awscli-local boto3 --upgrade
## Séquence 3 — Création de l’instance EC2
Récupération d’une image AMI
AMI_ID=$(awslocal ec2 describe-images \
  --query 'Images[0].ImageId' \
  --output text)
Création de l’instance
INSTANCE_ID=$(awslocal ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t2.micro \
  --query 'Instances[0].InstanceId' \
  --output text)
Vérification
echo $INSTANCE_ID

awslocal ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].State.Name'

Résultat attendu :

running
Création de la Lambda
Dossier
mkdir -p lambda
Fichier lambda/app.py
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
        return {"statusCode": 405, "body": "Use POST"}

    if path.endswith("/start"):
        ec2.start_instances(InstanceIds=[INSTANCE_ID])
        action = "started"

    elif path.endswith("/stop"):
        ec2.stop_instances(InstanceIds=[INSTANCE_ID])
        action = "stopped"

    else:
        return {"statusCode": 404, "body": "Unknown path"}

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
Packaging Lambda
cd lambda
zip function.zip app.py
cd ..
Création du rôle IAM
awslocal iam create-role \
  --role-name lambda-role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
Déploiement Lambda
awslocal lambda create-function \
  --function-name ec2-controller \
  --runtime python3.11 \
  --handler app.handler \
  --zip-file fileb://lambda/function.zip \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --environment Variables="{INSTANCE_ID=$INSTANCE_ID}"
Test direct Lambda
Stop
awslocal lambda invoke \
  --function-name ec2-controller \
  --payload '{"httpMethod":"POST","path":"/ec2/stop"}' \
  response.json

cat response.json
Start
awslocal lambda invoke \
  --function-name ec2-controller \
  --payload '{"httpMethod":"POST","path":"/ec2/start"}' \
  response.json

cat response.json
Création API Gateway
API
API_ID=$(awslocal apigateway create-rest-api \
  --name ec2-api \
  --query 'id' \
  --output text)

ROOT_ID=$(awslocal apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' \
  --output text)
Route /ec2
EC2_RESOURCE_ID=$(awslocal apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part ec2 \
  --query 'id' \
  --output text)
Route /ec2/start
START_RESOURCE_ID=$(awslocal apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $EC2_RESOURCE_ID \
  --path-part start \
  --query 'id' \
  --output text)

awslocal apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $START_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE

awslocal apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $START_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:ec2-controller/invocations
Route /ec2/stop
STOP_RESOURCE_ID=$(awslocal apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $EC2_RESOURCE_ID \
  --path-part stop \
  --query 'id' \
  --output text)

awslocal apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $STOP_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE

awslocal apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $STOP_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:ec2-controller/invocations
Déploiement API
awslocal apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name dev
Tests HTTP
Stop instance
curl -X POST http://$API_ID.execute-api.localhost.localstack.cloud:4566/dev/ec2/stop
Vérification
awslocal ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].State.Name'

Résultat :

stopped
Start instance
curl -X POST http://$API_ID.execute-api.localhost.localstack.cloud:4566/dev/ec2/start

Résultat :

running
Automatisation
Script Bash
./scripts/test-api.sh
Makefile
make start
make stop
make status
make test-api
Difficultés rencontrées
AWS CLI non trouvé

Erreur :

No such file or directory: aws

Solution :

pip install awscli awscli-local --upgrade
AMI inexistante

Erreur :

InvalidAMIID.NotFound

Solution :

awslocal ec2 describe-images