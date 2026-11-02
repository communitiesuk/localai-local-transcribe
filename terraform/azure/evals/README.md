# Azure Terraform for evals blob storage (AIILG-644, AIILG-649)

Provisions two storage accounts holding three private blob containers for pipeline data:

| Container | Account      | Purpose metadata | Reachable from            |
| --------- | ------------ | ---------------- | ------------------------- |
| `input`   | sensitive    | `purpose=input`  | ADAPT only                |
| `debug`   | sensitive    | `purpose=debug`  | ADAPT only                |
| `output`  | results      | `purpose=output` | ADAPT and MHCLG devices   |

## Why two accounts

Azure storage firewall rules and private endpoints are scoped to the storage account, not the container. AIILG-649 requires `input` and `debug` to be unreachable from MHCLG devices while `output` stays readable from them, at the network layer. The containers are therefore split across two accounts that differ only in the private endpoints that reach them.

## Controls

| Control                                        | Where                                          |
| ---------------------------------------------- | ---------------------------------------------- |
| Deny by default, public access off            | `network_rules` in `main.tf`                   |
| Private endpoint and private DNS for ADAPT      | `network.tf`                                   |
| Shared access keys disabled                    | `shared_access_key_enabled = false`, `main.tf` |
| Entra ID required for all data plane calls     | Follows from disabling shared keys             |
| Per-container RBAC, least privilege            | `rbac.tf`                                      |
| No public blobs, no local users, SAS expiry cap | `main.tf`                                      |
| Versioning, blob and container soft delete      | `main.tf`                                      |
| File and Blob diagnostic logs to Log Analytics  | `logging.tf`                                   |
| File and Blob diagnostic logs on the state account | `backend/logging.tf`                        |
| File service SMB 3.1.1, Kerberos, AES-256-GCM   | `share_properties` in `main.tf` and `backend/main.tf` |

Disabling shared access keys is what closes the Azure console bypass: with no account keys there is no account SAS and no "Access key" auth in the portal blob browser, so every read and write is an Entra ID call subject to the role assignments. This holds only while nobody has Owner, Contributor, or Storage Account Contributor on the resource group — those roles can re-enable keys. Keep them off it.

The parent root is applied by the Azure DevOps pipeline on the shared agents. `backend/`, `vnet/`, and `key-vault/` are applied from test ADAPT with local state. See Apply below.

## Azure DevOps pipeline identity

`pipeline_identity.tf` also provisions the identity the summarisation and bias eval pipelines use to
reach the blobs — a **user-assigned managed identity** federated to an Azure DevOps service
connection. `rbac.tf` grants it container-scoped data-plane roles: reader on `input`, contributor on
`debug`, and contributor on `output`. A managed identity is used rather than an Entra app
registration.

Federation needs the Issuer and Subject of the Azure DevOps service connection. Both are known before
the connection exists: the Issuer is `https://vstoken.dev.azure.com/<org-guid>` and the Subject is
`sc://<org>/<project>/evals-blob`. So one apply is enough:

1. Set `EVALS_ADO_FEDERATION_ISSUER` and `EVALS_ADO_FEDERATION_SUBJECT` in the variable group, then
   apply. This creates the identity, its roles, and the federated credential. Note the
   `pipeline_identity_client_id` output.
2. Create the ADO service connection `evals-blob` (**App registration or managed identity (manual)**,
   workload identity federation) using that client id. Check that the Issuer and Subject it shows
   match the variable group.

Creating the role assignments needs Owner or User Access Administrator on the relevant scope.

## Team container roles

`rbac.tf` also grants container roles to the object IDs in the variable group. `input_writer_principal_ids` can upload, change and delete blobs in `input`. `debug_reader_principal_ids` can read `debug`. `results_reader_principal_ids` can read `output`. `debug_and_output_writer_principal_ids` can read, write and delete blobs in both `debug` and `output`. An ad hoc evals run on test ADAPT writes both of those containers, so one list grants both roles. Storage Blob Data Contributor includes read and list, so those object IDs stay off the reader lists. Prefer a group object ID. A membership change inside the group takes effect without a Terraform apply. Adding or removing a group object ID from a list needs a plan and apply.

## Customer-managed key

The evals accounts encrypt with a customer-managed key from the vault in `key-vault/`.

- Settle encryption before anyone uploads data. `infrastructure_encryption_enabled` and the Table and
  Queue key type can only be set at create. Changing either replaces the account and deletes its blobs.
- Rotating or replacing the key does not touch the data. Disabling or deleting the key makes the data
  unreadable until the key is restored. Purge protection keeps a deleted key recoverable.
- A first apply can fail to wrap the key with a 403, because the new Key Vault role for
  `evals-storage-key-id` has not taken effect yet. Role assignments can take several minutes to apply
  ([Microsoft documentation](https://learn.microsoft.com/en-us/azure/role-based-access-control/troubleshooting#role-assignment-changes-are-not-being-detected)).
  Wait a few minutes and rerun the apply.

## Layout

| Path               | Role                                                               |
| ------------------ | ------------------------------------------------------------------ |
| `backend/`         | One-time bootstrap of remote Terraform state storage               |
| `main.tf`          | Both storage accounts, the three containers, firewall rules        |
| `logging.tf`       | File, Blob and vault diagnostic settings to the shared workspace   |
| `network.tf`       | Blob private endpoints                                             |
| `rbac.tf`          | Container-scoped role assignments                                  |
| `variables.tf`     | Input variables (required values plus optional hardening defaults) |
| `terraform.tfvars.example` | Example variable file for both Terraform roots             |

## Unknowns left as variables

The private endpoint subnet and principal IDs are variables. Empty network values deny that route except trusted Azure services using strong authentication.

## Private endpoints

`network.tf` creates one blob private endpoint per evals account, and one endpoint for the vault, in `private_endpoint_subnet_id`, the subnet created by `vnet/`. This root writes no Domain Name System records, because this subscription cannot write the hub `privatelink.blob.core.windows.net` and `privatelink.vaultcore.azure.net` zones. After an endpoint is created, the Azure team attaches it to its zone. Terraform ignores the zone group they add, so an apply does not remove it.

The vault in `key-vault/` denies public data-plane access. A plan of the parent root reads the key through the vault private endpoint. The shared agents reach the vault through that endpoint. Azure Storage encrypts the accounts with the customer-managed key through the `AzureServices` firewall exception.

## Logging

Every File and Blob read, write and delete on the three storage accounts, and every vault log category, go to the shared Log Analytics workspace that Cyber reads and that the team queries from outside test ADAPT. The workspace is in another subscription, set by `shared_log_analytics_workspace_id`. The identity that applies this root needs read and `Microsoft.OperationalInsights/workspaces/sharedKeys/action` on it. The parent root creates all seven settings, including those for the state account and the vault, so only the pipeline service principal needs those rights. Do not add a logging setting to `backend/` or `key-vault/`. The setting names end in `-shared` and must not be renamed, or Terraform would delete and recreate them.

Queue and Table diagnostic logging, a security information and event management system, and loading data into containers are still out of scope.

## Prerequisites

- Access to the test Azure tenant and subscription
- An existing resource group you are allowed to create storage accounts in
- Rights for the applying identity to create diagnostic settings that send to the shared Log Analytics workspace
- Three globally unique storage account names (3 to 24 lowercase letters and digits): one for Terraform state, one sensitive, one results
- A machine that reaches the state storage account's private endpoint, for `terraform init`, `plan`, and `apply` against the state backend
- Storage Blob Data Contributor on the state storage account (or `tfstate` container) for the identity that runs evals `terraform init`, `plan`, and `apply`, because remote state uses Entra ID (`use_azuread_auth=true`)
- User Access Administrator (or Owner) on the resource group for the applying identity, because `rbac.tf` creates role assignments

## Apply

The parent root is applied by the Azure DevOps pipeline on the shared agents. Remote state is the state storage account, container `tfstate`, key `evals-blob-containers.tfstate`. The applying identity needs Storage Blob Data Contributor on that state storage, and the shared agents reach it through the state private endpoint.

`backend/`, `vnet/`, and `key-vault/` are applied from test ADAPT. Each keeps its own local state on that profile. A copy of each state file is on SharePoint. If that profile is wiped, restore the copy before applying again.

Each root declares only the variables it uses. If a local file contains extra values from another root, Terraform ignores them and says so in a warning. `-compact-warnings` reduces that to a single summary line.

Blob reads go through the private endpoints, from test ADAPT or the shared agents. The Evals blob access check pipeline lists `input`, `debug`, and `output`.
