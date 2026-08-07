#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--environment <environment>] [--local-port <port>] [-- <psql args>]"
  echo ""
  echo "  Opens an SSM port-forwarding tunnel through the bastion to the RDS"
  echo "  database, then drops you into an interactive psql session."
  echo "  The tunnel is torn down automatically when you exit."
  echo ""
  echo "  --environment  Environment name (default: development)"
  echo "  --local-port   Local port to forward to (default: 5433)"
  echo ""
  echo "  Anything after '--' is passed straight to psql, e.g.:"
  echo "    $0 -- -c 'select count(*) from recordings'"
  echo "    $0 -- -f queries.sql"
  exit 1
}

ENVIRONMENT="development"
LOCAL_PORT="5433"

while [[ $# -gt 0 ]]; do
  case $1 in
    --environment) ENVIRONMENT="$2"; shift 2 ;;
    --local-port)  LOCAL_PORT="$2"; shift 2 ;;
    --help|-h)     usage ;;
    --)            shift; break ;;
    --*)           echo "Unknown option: $1"; usage ;;
    *)             break ;;
  esac
done

REGION="eu-west-2"
RDS_CERT_URL="https://truststore.pki.rds.amazonaws.com/${REGION}/${REGION}-bundle.pem"
RDS_CERT_DIR="${RDS_CA_BUNDLE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/local-transcribe}"
RDS_CERT_PATH="${RDS_CERT_PATH:-${RDS_CERT_DIR}/rds-ca-bundle-${REGION}.pem}"

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Error: '$1' is not installed. $2"; exit 1; }
}

require aws "Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
require curl "Install curl to download the RDS CA certificate bundle."
require session-manager-plugin "Install: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "Error: not authenticated to AWS."
  echo "Run: aws sso login --profile <your-profile> && export AWS_PROFILE=<your-profile>"
  exit 1
fi

download_rds_certificate_bundle() {
  if [[ -s "$RDS_CERT_PATH" ]]; then
    return
  fi

  echo "Downloading RDS CA certificate bundle to ${RDS_CERT_PATH}..."
  mkdir -p "$RDS_CERT_DIR"
  curl --fail --location --silent --show-error --output "${RDS_CERT_PATH}.tmp" "$RDS_CERT_URL"
  mv "${RDS_CERT_PATH}.tmp" "$RDS_CERT_PATH"
}

echo "Resolving connection details for '${ENVIRONMENT}'..."

BASTION_ID=$(aws ec2 describe-instances \
  --region "$REGION" \
  --filters "Name=tag:Name,Values=${ENVIRONMENT}-bastion-1" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].InstanceId" --output text)
if [[ -z "$BASTION_ID" || "$BASTION_ID" == "None" ]]; then
  echo "Error: no running bastion found for environment '${ENVIRONMENT}'."
  exit 1
fi

read -r DB_HOST DB_NAME < <(aws rds describe-db-instances \
  --region "$REGION" \
  --db-instance-identifier "${ENVIRONMENT}-database" \
  --query "DBInstances[0].[Endpoint.Address,DBName]" --output text)

DB_USER="postgres"

download_rds_certificate_bundle

echo "Opening tunnel to ${DB_HOST}:5432 via bastion ${BASTION_ID} (local port ${LOCAL_PORT})..."

aws ssm start-session \
  --region "$REGION" \
  --target "$BASTION_ID" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"${DB_HOST}\"],\"portNumber\":[\"5432\"],\"localPortNumber\":[\"${LOCAL_PORT}\"]}" &
SSM_PID=$!

trap 'kill "$SSM_PID" 2>/dev/null || true' EXIT

# Wait for the local port to start accepting connections.
for _ in $(seq 1 30); do
  if (exec 3<>"/dev/tcp/127.0.0.1/${LOCAL_PORT}") 2>/dev/null; then
    exec 3>&- 3<&-
    break
  fi
  sleep 1
done

DB_AUTH_TOKEN=$(aws rds generate-db-auth-token \
  --region "$REGION" \
  --hostname "$DB_HOST" \
  --port 5432 \
  --username "$DB_USER")

PGPASSWORD="$DB_AUTH_TOKEN" psql \
  "host=${DB_HOST} hostaddr=127.0.0.1 port=${LOCAL_PORT} user=${DB_USER} dbname=${DB_NAME} sslmode=verify-full sslrootcert=${RDS_CERT_PATH}" \
  "$@"
