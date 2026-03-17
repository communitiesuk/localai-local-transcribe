data "aws_iam_role" "ecs_task_execution" {
  name = "${local.environment_name}-ecs-task-execution"
}

data "aws_iam_role" "webapp_ecs_task" {
  name = "${local.environment_name}-webapp-ecs-task"
}

data "aws_ssm_parameter" "one_login_public_key" {
  name = "${local.environment_name}-one-login-public-key"
}

data "aws_ssm_parameter" "one_login_client_id" {
  name = "${local.environment_name}-one-login-client-id"
}

data "aws_ssm_parameter" "one_login_issuer_url" {
  name = "${local.environment_name}-one-login-issuer-url"
}

data "aws_ssm_parameter" "one_login_did_url" {
  name = "${local.environment_name}-one-login-did-url"
}

data "aws_ssm_parameter" "database_username" {
  name = "${local.environment_name}-prsdb-database-username"
}

data "aws_ssm_parameter" "database_url" {
  name = "${local.environment_name}-prsdb-database-url"
}

data "aws_secretsmanager_secret" "database_password" {
  name = "tf-${local.environment_name}-prsdb-database-password"
}

data "aws_ssm_parameter" "redis_url" {
  name = "${local.environment_name}-prsdb-redis-url"
}

data "aws_ssm_parameter" "redis_port" {
  name = "${local.environment_name}-prsdb-redis-port"
}

data "aws_secretsmanager_secret" "redis_password" {
  name = "tf-${local.environment_name}-prsdb-redis-password"
}

data "aws_secretsmanager_secret" "one_login_private_key" {
  name = "tf-${local.environment_name}-one-login-private-key"
}

data "aws_secretsmanager_secret" "notify_api_key" {
  name = "tf-${local.environment_name}-notify-api-key"
}

data "aws_secretsmanager_secret" "os_api_key" {
  name = "tf-${local.environment_name}-os-api-key"
}

data "aws_ssm_parameter" "quarantine_bucket" {
  count = var.file_upload_buckets_created ? 1 : 0
  name  = "${local.environment_name}-prsdb-quarantine-bucket"
}

data "aws_ssm_parameter" "safe_bucket" {
  count = var.file_upload_buckets_created ? 1 : 0
  name  = "${local.environment_name}-prsdb-uploaded-files"
}

data "aws_secretsmanager_secret" "epc_client_secret" {
  name = "tf-${local.environment_name}-prsdb-epc-client-secret"
}

data "aws_ssm_parameter" "epc_client_id" {
  name = "${local.environment_name}-prsdb-epc-client-id"
}

data "aws_ssm_parameter" "epc_token_uri" {
  name = "${local.environment_name}-prsdb-epc-token-uri"
}

data "aws_ssm_parameter" "epc_base_url" {
  name = "${local.environment_name}-prsdb-epc-register-base-url"
}

data "aws_ssm_parameter" "epc_certificate_base_url" {
  name = "${local.environment_name}-prsdb-epc-certificate-base-url"
}

data "aws_ssm_parameter" "landlord_base_url" {
  name = "${local.environment_name}-prsdb-landlord-base-url"
}

data "aws_ssm_parameter" "local_council_base_url" {
  name = "${local.environment_name}-prsdb-local-council-base-url"
}

data "aws_ssm_parameter" "plausible_analytics_domain_id" {
  name = "${local.environment_name}-prsdb-plausible-analytics-domain-id"
}

data "aws_ssm_parameter" "google_analytics_measurement_id" {
  name = "${local.environment_name}-prsdb-google-analytics-measurement-id"
}

data "aws_ssm_parameter" "google_analytics_cookie_domain" {
  name = "${local.environment_name}-prsdb-google-analytics-cookie-domain"
}

data "aws_ssm_parameter" "beta_feedback_team_email_address" {
  name = "${local.environment_name}-prsdb-beta-feedback-team-email-address"
}