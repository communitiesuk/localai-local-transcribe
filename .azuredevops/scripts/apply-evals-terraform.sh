#!/usr/bin/env bash
# Grant the applying service principal blob data access, allowlist this agent,
# then plan or apply terraform/azure/evals against remote state.
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
spn_app_id="$(az account show --query user.name -o tsv)"

# Contributor cannot do this. The pipeline service principal must already have
# User Access Administrator. Repeat runs skip create when the assignment exists.
existing_role="$(az role assignment list \
  --assignee "${spn_app_id}" \
  --role "Storage Blob Data Contributor" \
  --scope "${scope}" \
  --query "[0].id" -o tsv)"
if [ -z "${existing_role}" ]; then
  az role assignment create \
    --assignee "${spn_app_id}" \
    --assignee-principal-type ServicePrincipal \
    --role "Storage Blob Data Contributor" \
    --scope "${scope}"
fi

# Microsoft-hosted agents egress from a new IP each run. Remote state and
# azurerm storage refreshes both call the blob data plane, which the firewall
# denies unless this IP is listed.
agent_ip="$(curl -fsS https://api.ipify.org)"
for account_name in $(az storage account list --resource-group "${rg}" --query "[].name" -o tsv); do
  already="$(az storage account network-rule list \
    --account-name "${account_name}" \
    --resource-group "${rg}" \
    --query "ipRules[?ipAddressOrRange=='${agent_ip}'].ipAddressOrRange" -o tsv)"
  if [ -z "${already}" ]; then
    az storage account network-rule add \
      --account-name "${account_name}" \
      --resource-group "${rg}" \
      --ip-address "${agent_ip}"
  fi
done
# Firewall updates are not always visible on the data plane immediately.
sleep 30

cd terraform/azure/evals
cat > terraform.tfvars <<EOF
subscription_id     = "${sub}"
resource_group_name = "${rg}"
environment_name    = "${environment_name}"
sensitive_storage_account_name = "${sensitive_account}"
results_storage_account_name   = "${results_account}"
adapt_ip_rules = ["${adapt_ip}"]
mhclg_ip_rules = ["${adapt_ip}"]
ado_ip_rules   = ["${agent_ip}"]
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
