#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --environment <environment> --tag <tag> [frontend] [backend] [worker]"
  echo ""
  echo "  --environment  One of: development, staging, production (default: development)"
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

case "$ENVIRONMENT" in
  development|staging|production) ;;
  *) echo "Error: unknown environment '${ENVIRONMENT}' (must be development, staging, or production)"; usage ;;
esac

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
TF_DIR="${REPO_ROOT}/terraform/${ENVIRONMENT}"

if [[ ! -d "$TF_DIR" ]]; then
  echo "Error: no terraform configuration found at ${TF_DIR}"
  exit 1
fi

if [[ -z "${TF_VAR_alarm_email_address:-}" ]]; then
  echo "Error: TF_VAR_alarm_email_address is not set"
  exit 1
fi

SERVICES=("$@")
if [[ ${#SERVICES[@]} -eq 0 ]]; then
  SERVICES=(frontend backend worker)
fi

for SERVICE in "${SERVICES[@]}"; do
  case "$SERVICE" in
    frontend|backend|worker) ;;
    *) echo "Error: unknown service '${SERVICE}' (must be frontend, backend, or worker)"; exit 1 ;;
  esac
done

REGION="eu-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

case "$ENVIRONMENT" in
  development) EXPECTED_ACCOUNT_ALIAS="localtranscribe-Dev" ;;
  staging)     EXPECTED_ACCOUNT_ALIAS="localtranscribe-Staging" ;;
  production)  EXPECTED_ACCOUNT_ALIAS="localtranscribe-Prod" ;;
esac

ACCOUNT_ALIAS=$(aws iam list-account-aliases --query 'AccountAliases[0]' --output text)

if [[ "$ACCOUNT_ALIAS" != "$EXPECTED_ACCOUNT_ALIAS" ]]; then
  echo "Error: authenticated against AWS account alias '${ACCOUNT_ALIAS}', but ${ENVIRONMENT} expects '${EXPECTED_ACCOUNT_ALIAS}'."
  echo "Check AWS_PROFILE and try again."
  exit 1
fi

echo "Environment: ${ENVIRONMENT}"
echo "AWS account alias: ${ACCOUNT_ALIAS}"
echo "Image tag:   ${TAG}"

if [[ "$ENVIRONMENT" == "production" ]]; then
  echo ""
  echo "This will build and push images to PRODUCTION and then plan and apply Terraform against it."
  read -r -p "Type 'production' to continue: " confirm_env
  if [[ "$confirm_env" != "production" ]]; then
    echo "Aborted."
    exit 1
  fi
fi

REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "Authenticating with ECR..."
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY"

for SERVICE in "${SERVICES[@]}"; do
  REPO="${REGISTRY}/${ENVIRONMENT}-${SERVICE}"
  LOCAL_TAG="${ENVIRONMENT}-${SERVICE}:${TAG}"
  # Keep the array non-empty for Bash 3.2 with nounset (macOS).
  BUILD_ARGS=(-q)
  SENTRY_SECRET_FILE=""

  if [[ "$SERVICE" == "frontend" ]]; then
    BUILD_ARGS+=(--build-arg "NEXT_PUBLIC_SENTRY_DSN=${SENTRY_DSN:-}")
    BUILD_ARGS+=(--build-arg "NEXT_PUBLIC_POSTHOG_API_KEY=${POSTHOG_API_KEY:-}")
    BUILD_ARGS+=(--build-arg "NEXT_PUBLIC_ENVIRONMENT=${ENVIRONMENT:-}")

    if [[ -n "${SENTRY_AUTH_TOKEN:-}" ]]; then
      SENTRY_SECRET_FILE="$(mktemp)"
      printf '%s' "$SENTRY_AUTH_TOKEN" > "$SENTRY_SECRET_FILE"
      BUILD_ARGS+=(--secret "id=sentry_auth_token,src=$SENTRY_SECRET_FILE")
    else
      echo "Warning: SENTRY_AUTH_TOKEN not set; Sentry source upload will be skipped."
    fi
  fi

  echo ""
  echo "Building ${SERVICE}..."
  docker build "${BUILD_ARGS[@]}" -t "$LOCAL_TAG" -f "${REPO_ROOT}/${SERVICE}/Dockerfile" "$REPO_ROOT"

  # Best-effort cleanup; ignore failure if the file was already removed.
  if [[ -n "$SENTRY_SECRET_FILE" ]]; then
    rm -f "$SENTRY_SECRET_FILE"
  fi

  docker tag "$LOCAL_TAG" "${REPO}:${TAG}"

  echo "Pushing ${SERVICE}..."
  docker push --quiet "${REPO}:${TAG}"

  echo "${SERVICE} pushed as ${REPO}:${TAG}"
done

echo ""
echo "Planning Terraform..."
cd "$TF_DIR"
TF_VARS=(-var="image_tag=${TAG}")
terraform plan "${TF_VARS[@]}" -out=tfplan 2>&1 | grep -v ": Refreshing state\|: Reading\|: Still reading\|: Read complete"

echo ""
read -r -p "Apply the above plan? [y/N] " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }

echo "Applying..."
terraform apply -auto-approve tfplan
rm -f tfplan
cd "$REPO_ROOT"