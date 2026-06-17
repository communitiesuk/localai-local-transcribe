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


if [[ -z "${TF_VAR_alarm_email_address:-}" ]]; then
  echo "Error: TF_VAR_alarm_email_address is not set"
  exit 1
fi

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
cd "${REPO_ROOT}/terraform/${ENVIRONMENT}"
TF_VARS=(-var="image_tag=${TAG}")
terraform plan "${TF_VARS[@]}" -out=tfplan 2>&1 | grep -v ": Refreshing state\|: Reading\|: Still reading\|: Read complete"

echo ""
read -r -p "Apply the above plan? [y/N] " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }

echo "Applying..."
terraform apply -auto-approve tfplan
rm -f tfplan
cd "$REPO_ROOT"