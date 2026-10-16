#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--environment <env>] [--local-port <port>] [-- <aggregate_analytics args>]"
  echo ""
  echo "  Opens the DB tunnel (connect-to-aws-db.sh --tunnel-only), runs the aggregate analytics"
  echo "  report against it, then closes the tunnel."
  echo ""
  echo "  --environment  Environment name (default: development)"
  echo "  --local-port   Local port for the tunnel (default: 5433)"
  exit 1
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENVIRONMENT="development"
LOCAL_PORT="5433"
REGION="eu-west-2"

while [[ $# -gt 0 ]]; do
  case $1 in
    --environment) [[ $# -ge 2 ]] || usage; ENVIRONMENT="$2"; shift 2 ;;
    --local-port)  [[ $# -ge 2 ]] || usage; LOCAL_PORT="$2"; shift 2 ;;
    --help|-h)     usage ;;
    --)            shift; break ;;
    *)             break ;;
  esac
done

# Tunnel output goes to stderr so stdout stays clean for the JSON report.
"$ROOT/connect-to-aws-db.sh" --environment "$ENVIRONMENT" --local-port "$LOCAL_PORT" --tunnel-only >&2 &
TUNNEL_PID=$!
cleanup() {
  kill "$TUNNEL_PID" 2>/dev/null || true
  wait "$TUNNEL_PID" 2>/dev/null || true
}
trap cleanup EXIT

for _ in $(seq 1 60); do
  kill -0 "$TUNNEL_PID" 2>/dev/null || { echo "Error: tunnel exited before opening." >&2; exit 1; }
  (exec 3<>"/dev/tcp/127.0.0.1/${LOCAL_PORT}") 2>/dev/null && break
  sleep 1
done
(exec 3<>"/dev/tcp/127.0.0.1/${LOCAL_PORT}") 2>/dev/null || { echo "Error: tunnel not ready after 60s." >&2; exit 1; }

read -r RDS_HOST RDS_DB < <(aws rds describe-db-instances --region "$REGION" \
  --db-instance-identifier "${ENVIRONMENT}-database" \
  --query "DBInstances[0].[Endpoint.Address,DBName]" --output text)

export ENVIRONMENT AWS_REGION="$REGION"
# Stop the root .env's placeholder AWS keys (loaded by common.settings) overriding the SSO session.
export AWS_ACCESS_KEY_ID="" AWS_SECRET_ACCESS_KEY="" AWS_SESSION_TOKEN=""
export POSTGRES_HOST="${POSTGRES_HOST:-$RDS_HOST}"
export POSTGRES_DB="${POSTGRES_DB:-${RDS_DB/None/postgres}}"
export POSTGRES_USER="${POSTGRES_USER:-postgres}"
export POSTGRES_HOSTADDR=127.0.0.1 POSTGRES_PORT="$LOCAL_PORT" POSTGRES_IAM_PORT=5432
export RDS_CA_BUNDLE_PATH="${RDS_CA_BUNDLE_PATH:-${XDG_CACHE_HOME:-$HOME/.cache}/local-transcribe/rds-ca-bundle-${REGION}.pem}"

cd "$ROOT"
poetry run python -m reporting.aggregate_analytics "$@"
