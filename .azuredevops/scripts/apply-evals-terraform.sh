#!/usr/bin/env bash
# Grant the applying service principal blob data access on the Terraform state
# account, then plan or apply terraform/azure/evals against remote state.
#
# Required environment: EVALS_ARM_SUBSCRIPTION_ID, EVALS_RESOURCE_GROUP_NAME,
# EVALS_STATE_STORAGE_ACCOUNT_NAME, EVALS_ENVIRONMENT_NAME,
# EVALS_SENSITIVE_STORAGE_ACCOUNT_NAME, EVALS_RESULTS_STORAGE_ACCOUNT_NAME,
# EVALS_ADAPT_EGRESS_IP.
#
# Argument: plan or apply.

set -euo pipefail

terraform_command="${1:?pass plan or apply}"
if [ "${terraform_command}" != "plan" ] && [ "${terraform_command}" != "apply" ]; then
  echo "first argument must be plan or apply" >&2
  exit 1
fi

sub="${EVALS_ARM_SUBSCRIPTION_ID:?}"
rg="${EVALS_RESOURCE_GROUP_NAME:?}"
state_account="${EVALS_STATE_STORAGE_ACCOUNT_NAME:?}"
environment_name="${EVALS_ENVIRONMENT_NAME:?}"
sensitive_account="${EVALS_SENSITIVE_STORAGE_ACCOUNT_NAME:?}"
results_account="${EVALS_RESULTS_STORAGE_ACCOUNT_NAME:?}"
adapt_ip="${EVALS_ADAPT_EGRESS_IP:?}"

scope="/subscriptions/${sub}/resourceGroups/${rg}/providers/Microsoft.Storage/storageAccounts/${state_account}"
# Azure CLI 2.90: --assignee-principal-type must be paired with --assignee-object-id.
# The ARM access token oid claim is that Entra object ID, so Graph is not required.
spn_object_id="$(python3 -c "import json, base64, subprocess
token = subprocess.check_output(['az', 'account', 'get-access-token', '--query', 'accessToken', '-o', 'tsv'], text=True).strip()
payload = token.split('.')[1]
payload += '=' * ((-len(payload)) % 4)
print(json.loads(base64.urlsafe_b64decode(payload))['oid'])")"

# Contributor cannot do this. The pipeline service principal must already have
# User Access Administrator. Repeat runs skip create when the assignment exists.
existing_role="$(az role assignment list \
  --assignee "${spn_object_id}" \
  --role "Storage Blob Data Contributor" \
  --scope "${scope}" \
  --query "[0].id" -o tsv)"
if [ -z "${existing_role}" ]; then
  az role assignment create \
    --assignee-object-id "${spn_object_id}" \
    --assignee-principal-type ServicePrincipal \
    --role "Storage Blob Data Contributor" \
    --scope "${scope}"
fi

# This job must run on an agent whose traffic the state account firewall already
# allows: a self-hosted pool covered by a virtual network rule, or a pool with a
# stable public egress listed on the account. Allowlisting the agent IP at run
# time does not work on Microsoft-hosted agents, because Azure Storage ignores IP
# network rules for requests originating in the same region as the account, and a
# hosted agent may land in that region on any given run. See the Azure Storage
# firewall limitations: "IP network rules have no effect on requests that
# originate from the same Azure region as the storage account."
cd terraform/azure/evals
cat > terraform.tfvars <<EOF
subscription_id     = "${sub}"
resource_group_name = "${rg}"
environment_name    = "${environment_name}"
sensitive_storage_account_name = "${sensitive_account}"
results_storage_account_name   = "${results_account}"
adapt_ip_rules = ["${adapt_ip}"]
# No stable MHCLG-device IP yet (Zscaler). Results still allow the desktop via adapt_ip_rules.
mhclg_ip_rules = []
# Empty until the shared self-hosted pool exists and its egress address is known.
ado_ip_rules   = []
EOF

curl -fsSL "https://releases.hashicorp.com/terraform/1.16.2/terraform_1.16.2_linux_amd64.zip" -o /tmp/tf.zip
unzip -o /tmp/tf.zip -d /tmp
chmod +x /tmp/terraform

/tmp/terraform init -input=false \
  -backend-config="resource_group_name=${rg}" \
  -backend-config="storage_account_name=${state_account}" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=evals-blob-containers.tfstate" \
  -backend-config="use_azuread_auth=true"

if [ "${terraform_command}" = "apply" ]; then
  /tmp/terraform apply -input=false -auto-approve -compact-warnings
else
  /tmp/terraform plan -input=false -compact-warnings
fi
