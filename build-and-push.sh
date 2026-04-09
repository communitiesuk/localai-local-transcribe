#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --environment <environment> --tag <tag> [frontend] [backend] [worker]"
  echo ""
  echo "  --environment  Environment name (default: development)"
  echo "  --tag          Image tag to apply (default: current git short SHA)"
  echo ""
  echo "  Optionally specify one or more services to build (default: all)"
  echo "  Example: $0 --environment development --tag abc1234 backend worker"
  exit 1
}

ENVIRONMENT="development"
TAG="$(git rev-parse --short HEAD)"

while [[ $# -gt 0 ]]; do
  case $1 in
    --environment) ENVIRONMENT="$2"; shift 2 ;;
    --tag)         TAG="$2"; shift 2 ;;
    --*)           echo "Unknown option: $1"; usage ;;
    *)             break ;;
  esac
done


SERVICES=("$@")
if [[ ${#SERVICES[@]} -eq 0 ]]; then
  SERVICES=(frontend backend worker)
fi

REGION="eu-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "Authenticating with ECR..."
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY"

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

for SERVICE in "${SERVICES[@]}"; do
  case "$SERVICE" in
    frontend|backend|worker) ;;
    *) echo "Unknown service: $SERVICE (must be frontend, backend, or worker)"; exit 1 ;;
  esac

  REPO="${REGISTRY}/${ENVIRONMENT}-${SERVICE}"
  LOCAL_TAG="${ENVIRONMENT}-${SERVICE}:${TAG}"

  echo ""
  echo "Building ${SERVICE}..."
  docker build -q -t "$LOCAL_TAG" -f "${REPO_ROOT}/${SERVICE}/Dockerfile" "$REPO_ROOT"

  docker tag "$LOCAL_TAG" "${REPO}:${TAG}"

  echo "Pushing ${SERVICE}..."
  docker push --quiet "${REPO}:${TAG}"

  echo "${SERVICE} pushed as ${REPO}:${TAG}"
done

echo ""
echo "Planning Terraform..."
cd "${REPO_ROOT}/terraform/development"
TF_VARS=(-var="alarm_email_address=harry.best@softwire.com" -var="image_tag=${TAG}" -var="ssl_certs_created=false")
terraform plan "${TF_VARS[@]}" -out=tfplan 2>/dev/null | grep -v ": Refreshing state\|: Reading\|: Still reading\|: Read complete"

echo ""
read -r -p "Apply the above plan? [y/N] " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }

echo "Applying..."
terraform apply -auto-approve tfplan
rm -f tfplan
cd "$REPO_ROOT"

echo ""
echo "Waiting for frontend service to stabilise..."
aws ecs wait services-stable \
  --cluster "${ENVIRONMENT}-app" \
  --services "${ENVIRONMENT}-frontend" \
  --region "$REGION"

echo ""
echo "Looking up frontend task IP..."
TASK_ARN=$(aws ecs list-tasks \
  --cluster "${ENVIRONMENT}-app" \
  --family "frontend-${ENVIRONMENT}" \
  --query 'taskArns[0]' \
  --output text \
  --region "$REGION")

ENI_ID=$(aws ecs describe-tasks \
  --cluster "${ENVIRONMENT}-app" \
  --tasks "$TASK_ARN" \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text \
  --region "$REGION")

FRONTEND_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids "$ENI_ID" \
  --query 'NetworkInterfaces[0].PrivateIpAddress' \
  --output text \
  --region "$REGION")

echo "Frontend IP: ${FRONTEND_IP}"
echo ""
echo "Opening tunnel on http://localhost:3000 ..."
aws ssm start-session \
  --target i-0fe1661b5b3211bab \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"${FRONTEND_IP}\"],\"portNumber\":[\"3000\"],\"localPortNumber\":[\"3000\"]}" \
  --region "$REGION"
