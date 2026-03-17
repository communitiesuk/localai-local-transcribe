terraform {
  required_version = "~>1.9.1"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>5.0"
    }
  }

  backend "s3" {
    bucket         = "prsdb-tfstate-nft"
    dynamodb_table = "tfstate-lock-nft"
    encrypt        = true
    key            = "prsdb-infra-nft-task-definition"
    region         = "eu-west-2"
  }
}

locals {
  environment_name = "nft"
}

provider "aws" {
  region = "eu-west-2"
}

locals {
  common_environment_variables = [
    {
      name  = "ENVIRONMENT_NAME"
      value = local.environment_name
    },
    {
      name  = "RDS_URL"
      value = "jdbc:postgresql://${data.aws_ssm_parameter.database_url.value}"
    },
    {
      name  = "RDS_USERNAME"
      value = data.aws_ssm_parameter.database_username.value
    },
    # TODO PRSD-1325: Move bucket environment variables to ad-hoc tasks only when virus scan result processing is moved there
    {
      name  = "AWS_QUARANTINE_BUCKET"
      value = var.file_upload_buckets_created ? data.aws_ssm_parameter.quarantine_bucket[0].value : ""
    },
    {
      name  = "S3_SAFE_BUCKET_KEY"
      value = var.file_upload_buckets_created ? data.aws_ssm_parameter.safe_bucket[0].value : ""
    },
    {
      name  = "LANDLORD_BASE_URL"
      value = data.aws_ssm_parameter.landlord_base_url.value
    },
    {
      name  = "LOCAL_COUNCIL_BASE_URL"
      value = data.aws_ssm_parameter.local_council_base_url.value
    },
    {
      name  = "EMAILNOTIFICATIONS_USE_PRODUCTION_NOTIFY"
      value = contains(["production"], local.environment_name) ? "true" : "false"
    },
  ]
  webapp_only_environment_variables = [
    {
      name  = "ONE_LOGIN_PUBLIC_KEY"
      value = data.aws_ssm_parameter.one_login_public_key.value
    },
    {
      name  = "ONE_LOGIN_CLIENT_ID"
      value = data.aws_ssm_parameter.one_login_client_id.value
    },
    {
      name  = "ONE_LOGIN_ISSUER_URL"
      value = data.aws_ssm_parameter.one_login_issuer_url.value
    },
    {
      name  = "ONE_LOGIN_DID_URL"
      value = data.aws_ssm_parameter.one_login_did_url.value
    },
    {
      name  = "ELASTICACHE_URL"
      value = data.aws_ssm_parameter.redis_url.value
    },
    {
      name  = "ELASTICACHE_PORT"
      value = data.aws_ssm_parameter.redis_port.value
    },
    {
      name  = "EPC_REGISTER_CLIENT_ID"
      value = data.aws_ssm_parameter.epc_client_id.value
    },
    {
      name  = "EPC_REGISTER_TOKEN_URI"
      value = data.aws_ssm_parameter.epc_token_uri.value
    },
    {
      name  = "EPC_REGISTER_BASE_URL"
      value = data.aws_ssm_parameter.epc_base_url.value
    },
    {
      name  = "EPC_CERTIFICATE_BASE_URL"
      value = data.aws_ssm_parameter.epc_certificate_base_url.value
    },
    {
      name  = "PLAUSIBLE_ANALYTICS_DOMAIN_ID"
      value = data.aws_ssm_parameter.plausible_analytics_domain_id.value
    },
    {
      name  = "GOOGLE_ANALYTICS_MEASUREMENT_ID"
      value = data.aws_ssm_parameter.google_analytics_measurement_id.value
    },
    {
      name  = "GOOGLE_ANALYTICS_COOKIE_DOMAIN"
      value = data.aws_ssm_parameter.google_analytics_cookie_domain.value
    },
    {
      name  = "SPRING_PROFILES_ACTIVE"
      value = "default, ${local.environment_name}"
    },
    {
      name  = "BETA_FEEDBACK_TEAM_EMAIL_ADDRESS"
      value = data.aws_ssm_parameter.beta_feedback_team_email_address.value
    },
  ]
  # We set default Spring profiles for scheduled tasks to allow the application to correctly handle the case where a scheduled task is created without a dedicated profile. These should always be overridden by task-specific profiles.
  scheduled_tasks_only_environment_variables = [
    {
      name  = "SPRING_PROFILES_ACTIVE"
      value = "web-server-deactivated,scheduled-task"
    },
  ]
  common_secrets = [
    {
      name      = "RDS_PASSWORD"
      valueFrom = data.aws_secretsmanager_secret.database_password.arn
    },
    {
      name      = "EMAILNOTIFICATIONS_APIKEY"
      valueFrom = data.aws_secretsmanager_secret.notify_api_key.arn
    },
    {
      name      = "OS_API_KEY"
      valueFrom = data.aws_secretsmanager_secret.os_api_key.arn
    },
  ]
  webapp_secrets = [
    {
      name      = "ELASTICACHE_PASSWORD"
      valueFrom = data.aws_secretsmanager_secret.redis_password.arn
    },
    {
      name      = "ONE_LOGIN_PRIVATE_KEY"
      valueFrom = data.aws_secretsmanager_secret.one_login_private_key.arn
    },
    {
      name      = "EPC_REGISTER_CLIENT_SECRET"
      valueFrom = data.aws_secretsmanager_secret.epc_client_secret.arn
    },
  ]
}

module "webapp_ecs_task_definition" {
  source                      = "../../modules/ecs_task"
  environment_name            = local.environment_name
  container_image             = var.image_name
  container_port              = 8080
  ecs_task_execution_role_arn = data.aws_iam_role.ecs_task_execution.arn
  ecs_task_role_arn           = data.aws_iam_role.webapp_ecs_task.arn
  # TODO: consider what our requirements are for the instance
  task_cpu              = 512
  task_memory           = 1024
  task_name             = "prsdb-webapp"
  environment_variables = concat(local.common_environment_variables, local.webapp_only_environment_variables)
  secrets               = concat(local.common_secrets, local.webapp_secrets)
}

locals {
  scheduled_tasks = jsondecode(file("${path.module}/../scheduled_tasks.json"))
}

module "scheduled_tasks_ecs_task_definitions" {
  source                      = "../../modules/ecs_task"
  for_each                    = local.scheduled_tasks
  environment_name            = local.environment_name
  container_image             = var.image_name
  container_port              = 8080
  ecs_task_execution_role_arn = data.aws_iam_role.ecs_task_execution.arn
  ecs_task_role_arn           = data.aws_iam_role.webapp_ecs_task.arn
  # TODO: consider what our requirements are for the instance
  task_cpu              = 512
  task_memory           = 1024
  task_name             = "prsdb-${each.key}-scheduled-task"
  environment_variables = concat(local.common_environment_variables, local.scheduled_tasks_only_environment_variables)
  secrets               = local.common_secrets
  tags = {
    Type              = "scheduled-task"
    ScheduledTaskName = each.key
  }
}
